#import tadashi
from tadashi import TrEnum

from app import miniAMR

app = miniAMR(run_args=["--nx", "46", "--ny", "46", "--nz", "46"])


app.compile()
original_time = app.measure()
print(f"{original_time=}")
app.reset_scops()
trs = [
        [0, 6, TrEnum.FULL_SPLIT],
        #[0, 3, TrEnum.TILE2D, tile_size, tile_size],
        #[0, 9, TrEnum.TILE3D, tile_size, tile_size, tile_size],
    ]
app.transform_list(trs)
new_app = app.generate_code(ephemeral=False)
new_app.compile()
new_time = new_app.measure()
print(f"{new_time=}")
speedup = original_time /new_time
print(f"{speedup=}")

print("DONE")
