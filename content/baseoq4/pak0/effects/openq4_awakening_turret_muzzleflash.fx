// openQ4: muzzle flash for The Awakening's Strogg chaingun turret
// (common_turret_strogg). A hot orange Strogg flash with a forward streak, a
// pressure ring and a puff of propellant smoke per shot.
effect effects/openq4/awakening/turret_muzzleflash
{
	size	120

	spawner "flash_core"
	{
		count		1,1
		locked

		sprite
		{
			duration	0.05,0.05
			material	"gfx/effects/weapons/mgun_muzzleflash"

			start
			{
				size { box 18,18,24,24 }
				tint { point 1,0.78,0.55 }
				fade { point 0 }
				rotate { box 0,1 }
			}

			motion
			{
				size { envelope "linear" }
				fade { envelope "cosine" }
				rotate { envelope "linear" }
			}

			end
			{
				size { box 6,6,8,8 }
				fade { point 1 }
				rotate { box -0.5,0.5 relative }
			}
		}
	}
	spawner "flash_side"
	{
		count		2,2
		locked

		sprite
		{
			duration	0.05,0.05
			material	"gfx/effects/weapons/flash"

			start
			{
				position { point 4,0,0 }
				size { box 34,11,40,13 }
				tint { point 1,0.62,0.32 }
				fade { point 0 }
				rotate { box -0.12,0.12 }
			}

			motion
			{
				size { envelope "linear" }
				fade { envelope "cosine" }
			}

			end
			{
				size { box 4,3,5,4 }
				fade { point 0.25 }
			}
		}
	}
	spawner "streak"
	{
		count		1,1
		locked

		line
		{
			duration	0.05,0.05
			blend	add
			material	"gfx/effects/weapons/flash_half4"

			start
			{
				size { point 8 }
				tint { point 1,0.7,0.42 }
				length { box 50,0,0,75,0,0 }
			}

			motion
			{
				size { envelope "linear" }
				fade { envelope "linear" }
				length { envelope "linear" }
			}

			end
			{
				size { point 3 }
			}
		}
	}
	spawner "pressure_ring"
	{
		count		1,1
		locked

		oriented
		{
			duration	0.16,0.16
			blend	add
			material	"gfx/effects/weapons/railgun_ring"

			start
			{
				position { point 2,0,0 }
				velocity { box 120,0,0,180,0,0 }
				size { box 14,14,18,18 }
				tint { point 1,0.55,0.25 }
				fade { point 0 }
			}

			motion
			{
				size { envelope "linear" }
				fade { envelope "fastinslowout" }
			}

			end
			{
				size { box 34,34,42,42 }
				fade { point 0.12 }
			}
		}
	}
	spawner "embers"
	{
		count		1,3

		sprite
		{
			duration	0.12,0.2
			blend	add
			material	"gfx/effects/particles_shapes/blank"
			gravity		0.3,0.5
			trailType	motion
			trailTime	0.05,0.05
			trailCount	2,2

			start
			{
				velocity { box 250,-80,-80,420,80,80 }
				size { box 1.5,1.5,2.5,2.5 }
				tint { point 1,0.68,0.3 }
			}

			motion
			{
				size { envelope linear }
				tint { envelope linear }
			}

			end
			{
				size { point 0.5,0.5 }
				tint { point 0.8,0.25,0.05 }
			}
		}
	}
	spawner "smoke"
	{
		count		1,1

		sprite
		{
			duration	0.7,0.9
			material	"gfx/effects/smoke/cloud_alpha3"
			gravity		-0.3,-0.3

			start
			{
				position { point 6,0,0 }
				velocity { box 40,-10,-10,80,10,10 }
				size { point 8,8 }
				tint { line 0.47,0.45,0.42,0.42,0.4,0.37 }
				fade { point 0 }
				rotate { box -0.4,0.4 }
			}

			motion
			{
				size { envelope "linear" }
				tint { envelope "linear" }
				fade { envelope "fastinslowout" }
				rotate { envelope "linear" }
			}

			end
			{
				size { point 34,34 }
				fade { point 0.18 }
				rotate { box -0.5,0.5 relative }
			}
		}
	}
}
