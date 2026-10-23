#!/usr/bin/env python3
"""Run the production touch preference/transaction and JNI foreground boundaries."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess

from filesystem_case_segments import function_body

ROOT = Path(__file__).resolve().parents[2]
JAVA = r'''
package com.darkmatter.openq4;
import java.util.*;
public class TouchSetupTest {
    static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    static class SharedPreferences {
        Map<String,String> memory=new HashMap<>(),disk=new HashMap<>(); boolean fail;
        String getString(String key,String fallback){return memory.getOrDefault(key,fallback);}
        Editor edit(){return new Editor();}
        class Editor {
            Map<String,String> writes=new HashMap<>();
            Editor putString(String key,String value){writes.put(key,value);return this;}
            Editor remove(String key){return putString(key,null);}
            boolean commit(){applyMemory();if(fail)return false;disk=new HashMap<>(memory);return true;}
            void apply(){applyMemory();if(!fail)disk=new HashMap<>(memory);}
            void applyMemory(){writes.forEach((key,value)->{if(value==null)memory.remove(key);else memory.put(key,value);});}
        }
    }
    static class Host {
        static final int MODE_PRIVATE=0; final SharedPreferences prefs=new SharedPreferences();
        SharedPreferences getSharedPreferences(String name,int mode){check(name.equals("setup") && mode==0,"wrong preferences");return prefs;}
        @GETTER@
    }
    static class StorageSession {
        static final StorageSession INSTANCE=new StorageSession();boolean active,closing;
        boolean gameActive(){return active || closing;}boolean activityActive(){return active;}
    }
    static class View {static final int VISIBLE=0,GONE=8;}
    static class ReturnButton {int visibility=-1;void setVisibility(int value){visibility=value;}}
    static class Refresh {
        boolean pending;int posts;
        void removeCallbacks(Runnable value){pending=false;}
        void postDelayed(Runnable value,int delay){check(delay==500,"unbounded return poll");pending=true;++posts;}
    }
    static class Launcher {
        ReturnButton returnGame=new ReturnButton();Refresh refresh=new Refresh();boolean started=true;
        Runnable refreshState=()->{};
        @RETURN@
    }
    @SAVE@
    public static void main(String[] args){
        for(int p=0;p<3;p++)for(int s=1;s<=40;s++)for(int z=0;z<=15;z++){
            TouchSettings a=new TouchSettings(p,s,z),b=TouchSettings.decode(a.encode());
            check(Arrays.equals(a.engineValues(),b.engineValues()),"preference round trip");
        }
        for(String value:new String[]{null,"","2:0:10:5","1:3:10:5","1:0:0:5","1:0:41:5","1:0:10:16","1:-1:10:5","1:0:NaN:5","1:0:10:5:6","1:0:10:5\n"})
            check(TouchSettings.decode(value)==TouchSettings.DEFAULT,"malformed record accepted: "+value);
        check(TouchSettings.lookDegrees(80,2,1.5f)==15,"look test differs from physical-dp gameplay sensitivity");
        check(TouchSettings.lookDegrees(-40,1,2)==-20,"look test inverted a delta");
        check(TouchSettings.lookDegrees(0,1,4)==0,"stationary pointer moves preview");
        for(float v:new float[]{Float.NaN,Float.POSITIVE_INFINITY,0,-1,17})
            check(TouchSettings.lookDegrees(40,v,1)==0,"invalid density accepted");
        Host host=new Host();SharedPreferences prefs=host.prefs;
        check(host.getTouchSetup()==null,"unconfigured launcher overwrote engine preferences");
        TouchSettings draft=new TouchSettings(2,15,8);
        prefs.edit().putString(TouchSettings.DRAFT,draft.encode()).apply();
        check(host.getTouchSetup()==null,"draft reached engine");
        prefs.fail=true;check(!saveApplied(prefs,draft),"failed storage reported success");
        check(host.getTouchSetup()==null && prefs.memory.get(TouchSettings.DRAFT).equals(draft.encode()),"first failed apply did not restore absence/draft");
        prefs.fail=false;check(saveApplied(prefs,draft),"valid apply rejected");
        check(Arrays.equals(host.getTouchSetup(),draft.engineValues()) && !prefs.memory.containsKey(TouchSettings.DRAFT),"applied record not delivered atomically");
        check(prefs.memory.equals(prefs.disk),"saved record did not survive process restart");
        TouchSettings next=new TouchSettings(1,8,3);prefs.fail=true;
        check(!saveApplied(prefs,next) && Arrays.equals(host.getTouchSetup(),draft.engineValues()),"failed update changed live engine settings");
        check(prefs.memory.get(TouchSettings.DRAFT).equals(next.encode()),"failed update lost draft");
        Launcher launcher=new Launcher();StorageSession.INSTANCE.active=true;
        check(launcher.refreshGameReturn() && launcher.returnGame.visibility==View.VISIBLE && launcher.refresh.pending,"live return missing on non-data page");
        StorageSession.INSTANCE.active=false;StorageSession.INSTANCE.closing=true;
        check(launcher.refreshGameReturn() && launcher.returnGame.visibility==View.GONE && launcher.refresh.pending,"closing engine lease stopped refreshing");
        StorageSession.INSTANCE.closing=false;
        check(!launcher.refreshGameReturn() && !launcher.refresh.pending,"ended engine still polls");
        launcher.started=false;StorageSession.INSTANCE.active=true;launcher.refreshGameReturn();
        check(!launcher.refresh.pending,"stopped Activity scheduled refresh");
        System.out.println("PASS: 1920 preference round trips, malformed recovery, look scaling, draft isolation, initial/update commit failure, process persistence and actual Activity getter");
    }
}
'''
NATIVE = r'''
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <set>
using jobject=void*;using jclass=void*;using jmethodID=void*;using jfloatArray=void*;using jfloat=float;
static void check(bool value,const char* message){if(!value){std::fprintf(stderr,"FAIL: %s\n",message);std::exit(1);}}
struct JNIEnv {
    int failure=0,length=3;bool exception=false;std::set<void*> deleted;float data[3]={2,1.5f,1.25f};
    jclass GetObjectClass(jobject){if(failure==1){exception=true;return nullptr;}return (void*)2;}
    jmethodID GetMethodID(jclass,const char*,const char*){if(failure==2){exception=true;return nullptr;}return (void*)3;}
    jobject CallObjectMethod(jobject,jmethodID){if(failure==3){exception=true;return nullptr;}return failure==4?nullptr:(void*)4;}
    bool ExceptionCheck(){return exception;}void ExceptionClear(){exception=false;}
    int GetArrayLength(jfloatArray){return length;}
    void GetFloatArrayRegion(jfloatArray,int,int n,jfloat* out){if(failure==5){exception=true;return;}std::copy(data,data+n,out);}
    void DeleteLocalRef(jobject obj){check(deleted.insert(obj).second,"double local-ref release");}
} env;
static bool noEnv=false,noActivity=false;
static void* SDL_GetAndroidJNIEnv(){return noEnv?nullptr:&env;}
static void* SDL_GetAndroidActivity(){return noActivity?nullptr:(void*)1;}
struct Cvar{float value=0;int sets=0;void SetInteger(int v){value=v;++sets;}void SetFloat(float v){value=v;++sets;}}
    in_touchLayoutPreset,in_touchLookSensitivity,in_touchControlsScale;
struct Common{void Warning(const char*){}} commonObject,*common=&commonObject;
@FUNCTION@
static void reset(){env=JNIEnv{};noEnv=noActivity=false;in_touchLayoutPreset=Cvar{};in_touchLookSensitivity=Cvar{};in_touchControlsScale=Cvar{};}
static void unchanged(){check(!in_touchLayoutPreset.sets && !in_touchLookSensitivity.sets && !in_touchControlsScale.sets,"invalid setup partially changed cvars");}
int main(){
    reset();TouchControls_LoadSetup();
    check(in_touchLayoutPreset.value==2 && in_touchLookSensitivity.value==1.5f && in_touchControlsScale.value==1.25f,"valid setup not applied");
    check(env.deleted==std::set<void*>({(void*)1,(void*)2,(void*)4}),"JNI locals leaked");
    for(int failure=1;failure<=5;++failure){reset();env.failure=failure;TouchControls_LoadSetup();unchanged();check(!env.exception && env.deleted.count((void*)1),"exception or Activity reference leaked");}
    for(int n:{0,1,2,4}){reset();env.length=n;TouchControls_LoadSetup();unchanged();}
    for(auto invalid:{std::pair<int,float>{0,-1},{0,3},{0,1.5f},{1,0},{1,5},{2,0},{2,2},{0,NAN},{1,NAN},{2,INFINITY}}){reset();env.data[invalid.first]=invalid.second;TouchControls_LoadSetup();unchanged();}
    reset();noEnv=true;TouchControls_LoadSetup();unchanged();check(env.deleted.empty(),"JNI call without env");
    reset();noActivity=true;TouchControls_LoadSetup();unchanged();check(env.deleted.empty(),"JNI call without Activity");
    std::puts("PASS: production JNI foreground preference bridge, exact payload validation, missing/unconfigured host, exceptions and local-reference ownership");
}
'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--javac', default=shutil.which('javac') or str(Path(os.environ.get('JAVA_HOME', ''))/'bin/javac.exe'))
    parser.add_argument('--cxx', default=os.environ.get('CXX') or shutil.which('clang++') or shutil.which('g++'))
    args = parser.parse_args()
    out = ROOT/'.tmp/android-touch-setup'
    out.mkdir(parents=True, exist_ok=True)
    production = ROOT/'mobile/android/app/src/main/java/com/darkmatter/openq4'
    java_source = JAVA.replace('@GETTER@', function_body((production/'OpenQ4Activity.java').read_text(), 'public float[] getTouchSetup('))
    java_source = java_source.replace('@SAVE@', function_body((production/'ControlsPage.java').read_text(), 'static boolean saveApplied('))
    launcher = (production/'LauncherActivity.java').read_text()
    java_source = java_source.replace('@RETURN@', function_body(launcher, 'private boolean refreshGameReturn('))
    changed = function_body(launcher, 'public void changed(')
    assert changed.index('refreshGameReturn()') < changed.index('if (status == null)'), 'non-data page skips native ownership refresh'
    unit = out/'TouchSetupTest.java'; unit.write_text(java_source, encoding='utf-8')
    classes = out/'classes'; classes.mkdir(exist_ok=True)
    javac = Path(args.javac).resolve()
    subprocess.run([str(javac), '--release', '17', '-d', str(classes), str(production/'TouchSettings.java'), str(unit)], check=True)
    subprocess.run([str(javac.with_name('java.exe' if os.name=='nt' else 'java')), '-cp', str(classes), 'com.darkmatter.openq4.TouchSetupTest'], check=True)
    cpp = out/'jni.cpp'; binary = out/('jni.exe' if os.name=='nt' else 'jni')
    glue = (ROOT/'src/sys/android/android_touch_controls.cpp').read_text()
    cpp.write_text(NATIVE.replace('@FUNCTION@', function_body(glue, 'static void TouchControls_LoadSetup(')), encoding='utf-8')
    env = {**os.environ, 'TMP':str(out), 'TEMP':str(out), 'TMPDIR':str(out)}
    subprocess.run([args.cxx, '-std=c++17', '-O1', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(binary)], env=env, cwd=out, check=True)
    subprocess.run([str(binary)], check=True)

if __name__ == '__main__':
    main()
