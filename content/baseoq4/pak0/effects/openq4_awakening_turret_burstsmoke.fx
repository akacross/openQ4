// openQ4: smoke curling from the Strogg chaingun turret's muzzle after a
// long burst (rvVehicleWeapon "fx_burstSmoke").
effect effects/openq4/awakening/turret_burstsmoke
{
	size	48

	emitter "wisps"
	{
		duration	1.8,1.8
		count		20,20

		sprite
		{
			duration	1.6,2.4
			material	"gfx/effects/smoke/cloud_alpha2"
			gravity		-0.15,-0.2

			start
			{
				velocity { box 5,-3,-3,15,3,3 }
				size { point 3,3 }
				tint { line 0.58,0.56,0.53,0.5,0.48,0.45 }
				fade { point 0.42 }
				rotate { box 0,1 }
			}

			motion
			{
				size { envelope "linear" }
				fade { envelope "linear" }
				rotate { envelope "linear" }
			}

			end
			{
				size { box 14,14,20,20 }
				fade { point 0 }
				rotate { box -0.3,0.3 relative }
			}
		}
	}
	emitter "heat_trail"
	{
		duration	0.8,0.8
		count		6,6

		line
		{
			duration	0.9,1.2
			material	"gfx/effects/smoke/soft_alpha_trail"

			start
			{
				velocity { box 4,-2,-2,10,2,2 }
				size { box 1.5,2.5 }
				tint { point 0.55,0.53,0.5 }
				fade { point 0.35 }
				length { point 8,0,0 }
			}

			motion
			{
				size { envelope "linear" }
				fade { envelope "linear" }
			}

			end
			{
				size { box 5,7 }
				fade { point 0 }
			}
		}
	}
}
