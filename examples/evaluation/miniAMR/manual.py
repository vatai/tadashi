#import tadashi
from tadashi import TrEnum

from app import miniAMR

app = miniAMR(run_args=["--nx", "42", "--ny", "42", "--nz", "42"])


app.compile()
print(f"{app.measure()=}")
app.reset_scops()
trs = [
        [0, 6, TrEnum.FULL_SPLIT],
        #[0, 3, TrEnum.TILE2D, tile_size, tile_size],
        #[0, 9, TrEnum.TILE3D, tile_size, tile_size, tile_size],
    ]
app.transform_list(trs)
new_app = app.generate_code(ephemeral=False)

new_app.compile()
print(f"{new_app.measure()=}")

print("DONE")
