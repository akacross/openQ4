// openQ4: tracer for The Awakening's Strogg chaingun turret. A hot orange
// line with a faint halo, from the muzzle to where the round lands.
effect effects/openq4/awakening/turret_tracer
{
	size	3

	spawner "tracer"
	{
		count		1,1
		locked

		line
		{
			duration	0.08,0.08
			blend	add
			material	"gfx/effects/weapons/tracerflipped"

			start
			{
				size { box 3.5,4.5 }
				tint { point 1,0.62,0.3 }
				length { line 0,0,0,0,0,0 useEndOrigin }
			}

			motion
			{
				fade { envelope linear }
				length { envelope linear }
			}
		}
	}
	spawner "halo"
	{
		count		1,1
		locked

		line
		{
			duration	0.06,0.06
			blend	add
			material	"gfx/effects/weapons/tracerflipped"

			start
			{
				size { box 11,14 }
				tint { point 0.6,0.27,0.08 }
				length { line 0,0,0,0,0,0 useEndOrigin }
			}

			motion
			{
				fade { envelope linear }
				length { envelope linear }
			}
		}
	}
}
