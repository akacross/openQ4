#!/usr/bin/env python3
"""The Awakening's mannable Strogg chaingun turret has a finished skin and
the effects its alpha content left out (docs/user/awakening.md).

- openQ4's materials for model common_turret_strogg load ahead of the
  expansion's q4x_mapobjects.mtr, use openQ4's own colour, specular and glow
  maps (all present in pak0), and keep the expansion's normal maps, which
  openQ4 never ships.
- Under q4xbase idGameLocal::FindEntityDef finds "<name>_q4x_openq4" first;
  the turret's weapon definition inherits the expansion's and only adds
  presentation (muzzle flash and light, tracers, casings, barrel smoke).
- A vehicle weapon ejects casings at all (Raven's timing test returned on
  every shot) in its joint's frame, and trails "fx_burstSmoke" after a burst
  of "burstSmokeShots" or more; neither is saved.
- materials/*_openq4.mtr files re-declare a game's materials without a
  "previously defined" warning, as def/*_openq4.def files already did.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAK0 = ROOT / "content" / "baseoq4" / "pak0"
MATERIAL_FILE = "materials/00_awakening_turret_openq4.mtr"
DEF_FILE = "def/vehicles/awakening_turret_openq4.def"
TURRET_MATERIALS = [f"models/mapobjects/q4x/common_turret_strogg/common_turret_strogg0{i}" for i in range(1, 5)]


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"Required file not found: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def function_body(source: str, signature: str, context: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise AssertionError(f"Missing {signature!r} in {context}")
    brace = source.find("{", start + len(signature))
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace:index + 1]
    raise AssertionError(f"Unterminated {signature!r} in {context}")


def decl_bodies(text: str) -> dict[str, str]:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    bodies = {}
    for match in re.finditer(r"(?:entityDef\s+)?([A-Za-z0-9_/]+)\s*\{", text):
        if match.start() and text[:match.start()].count("{") != text[:match.start()].count("}"):
            continue
        depth = 0
        for index in range(match.end() - 1, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    bodies[match.group(1)] = text[match.end():index]
                    break
    return bodies


def check_find_entity_def() -> None:
    source = read(ROOT / "src/game/Game_local.cpp")
    body = function_body(source, "const idDeclEntityDef *idGameLocal::FindEntityDef(", "Game_local.cpp")
    mp = body.find('"%s_mp"')
    q4x = body.find('"%s_q4x_openq4"')
    assert mp >= 0 and q4x > mp, "multiplayer keeps its _mp redirect; the Awakening one is single player only"
    assert re.search(r'else if \(.*GetActiveGameDir\(\), "q4xbase" \)', body), "the _q4x_openq4 redirect is scoped to q4xbase"
    assert body.count("FindType( DECL_ENTITYDEF, name, makeDefault )") == 1, "the plain name stays the fallback"


def check_vehicle_weapon() -> None:
    source = read(ROOT / "src/game/vehicle/VehicleParts.cpp")
    header = read(ROOT / "src/game/vehicle/VehicleParts.h")
    eject = function_body(source, "void rvVehicleWeapon::EjectBrass ( void )", "VehicleParts.cpp")
    assert "gameLocal.time > brassEjectNext" not in eject, "Raven's inverted timing test is gone"
    assert "gameLocal.time < brassEjectNext" in eject and "brassEjectNext = gameLocal.time + brassEjectDelay" in eject
    assert "GetPlayerView" not in eject and "weaponDepthHackInViewID" not in eject, "casings use the joint frame, not the view"
    assert "cent->SetAxis ( axis );" in eject
    assert "g_brassTime.GetFloat() / 2.0f" in eject, "casings live as long as a hand-held weapon's"

    assert "void\t\t\t\t\tEndBurst\t\t\t( void );" in header
    assert re.search(r"int\s+burstShots;", header) and re.search(r"int\s+burstSmokeShots;", header)
    end = function_body(source, "void rvVehicleWeapon::EndBurst( void )", "VehicleParts.cpp")
    assert "burstSmokeShots <= 0" in end and '"fx_burstSmoke"' in end
    post = function_body(source, "void rvVehicleWeapon::RunPostPhysics ( void )", "VehicleParts.cpp")
    assert re.search(r"BUTTON_ATTACK \) \) \{\s*EndBurst\(\);\s*return;", post), "letting go of the trigger ends the burst"
    fire = function_body(source, "bool rvVehicleWeapon::Fire()", "VehicleParts.cpp")
    assert "burstShots++;" in fire
    spawn = function_body(source, "void rvVehicleWeapon::Spawn ( void )", "VehicleParts.cpp")
    restore = function_body(source, "void rvVehicleWeapon::Restore ( idRestoreGame* savefile )", "VehicleParts.cpp")
    save = function_body(source, "void rvVehicleWeapon::Save ( idSaveGame* savefile ) const", "VehicleParts.cpp")
    for name, body in (("Spawn", spawn), ("Restore", restore)):
        assert 'burstSmokeShots = spawnArgs.GetInt( "burstSmokeShots", "0" );' in body, f"{name} reads burstSmokeShots"
    assert "burst" not in save.lower(), "burst state is presentation only and never saved"


def check_decl_override_files() -> None:
    source = read(ROOT / "src/framework/DeclManager.cpp")
    body = function_body(source, "static bool DeclManager_IsopenQ4OverrideDeclFile(", "DeclManager.cpp")
    assert '"_openq4.def"' in body and '"materials/"' in body and '"_openq4.mtr"' in body


def check_content() -> None:
    material_path = PAK0 / MATERIAL_FILE
    assert Path(MATERIAL_FILE).name < "q4x_mapobjects.mtr", "the override must sort ahead of the expansion's file"
    materials = decl_bodies(read(material_path))
    for name in TURRET_MATERIALS:
        assert name in materials, f"{name} is re-declared"
        body = materials[name]
        bump = re.search(r"bumpmap\s+(\S+)", body)
        assert bump and bump.group(1) == name + "_local.tga", f"{name} keeps the expansion's normal map"
        for image in re.findall(r"(models/openq4/awakening/\S+\.(?:jpg|tga))", body):
            assert (PAK0 / image).is_file(), f"{name} names a missing image {image}"
        assert re.search(r"diffusemap|blend\s+diffusemap", body) and "specularmap" in body
    assert "alphatest" in materials[TURRET_MATERIALS[1]], "the drum's windows stay cut out"
    assert "twoSided" in materials[TURRET_MATERIALS[3]], "the rounds show through the front windows too"
    for index in (0, 2):
        assert "blend\t\tadd" in materials[TURRET_MATERIALS[index]], "sensor lens and vent glow stages"

    defs = decl_bodies(read(PAK0 / DEF_FILE))
    weapon = defs.get("vehicle_chaingun_weapon_q4x_openq4")
    assert weapon is not None, "the turret weapon's Awakening definition"
    assert re.search(r'"inherit"\s+"vehicle_chaingun_weapon"', weapon)
    for balance_key in ("def_damage", "firedelay", "spread", "count", "force"):
        assert f'"{balance_key}"' not in weapon, f"presentation only: {balance_key} stays the expansion's"
    hitscan = re.search(r'"def_hitscan"\s+"([^"]+)"', weapon).group(1)
    assert hitscan in defs and '"inherit"\t\t\t\t"hitscan_bullet"' in defs[hitscan]
    assert '"def_damage"' not in defs[hitscan]
    brass = re.search(r'"def_ejectBrass"\s+"([^"]+)"', weapon).group(1)
    assert brass in defs and re.search(r'"spawnclass"\s+"rvClientMoveable"', defs[brass]), "casings are client moveables"
    # pak0 has no directory entries, so the decl manager never lists a folder
    # only openQ4 adds: its effect files sit directly in effects/ and carry the
    # longer decl name inside, like the liquids effects
    declared = {}
    for fx_file in (PAK0 / "effects").glob("*.fx"):
        match = re.search(r"^effect\s+(\S+)", read(fx_file), re.M)
        assert match, f"{fx_file.name} declares an effect"
        declared[match.group(1)] = fx_file
    referenced = re.findall(r'"(effects/openq4/awakening/[^"]+)\.fx"', read(PAK0 / DEF_FILE))
    assert len(referenced) == 3, "muzzle flash, tracer and burst smoke"
    for effect in referenced:
        assert effect in declared, f"{effect} is declared by a file directly in pak0/effects"
    nested = [p for p in (PAK0 / "effects").rglob("*.fx") if p.parent != PAK0 / "effects"]
    assert not nested, f"effect files below effects/ are never loaded from pak0: {nested}"

    shipped = [p for p in PAK0.rglob("*") if p.is_file() and "mapobjects/q4x" in p.as_posix()]
    assert not shipped, f"openQ4 never ships expansion paths: {shipped}"


def main() -> None:
    check_find_entity_def()
    check_vehicle_weapon()
    check_decl_override_files()
    check_content()
    print("awakening_turret_skin_contract: ok")


if __name__ == "__main__":
    main()
