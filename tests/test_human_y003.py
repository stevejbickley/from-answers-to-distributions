import pandas as pd
from src.human import clean


def test_y003_is_filled_rowwise_from_constituents_when_structurally_missing():
    # Include the minimum fields expected by clean() and one valid WVS-like Y003
    # plus one EVS-like structural missing Y003 (-3).
    df = pd.DataFrame({
        'S002VS':[7,7], 'S017':[1.0,1.0], 'S020':[2018,2018],
        'A008':[1,1], 'A165':[1,1], 'E018':[1,1], 'E025':[1,1],
        'F063':[1,1], 'F118':[1,1], 'F120':[1,1], 'G006':[1,1],
        'Y002':[1,1], 'Y003':[-3, 2],
        'A029':[1,1], 'A039':[1,1], 'A040':[0,0], 'A042':[1,0],
    })
    out = clean(df)
    assert out.loc[0,'Y003'] == 1  # 1 + 1 - 0 - 1
    assert out.loc[1,'Y003'] == 2  # existing valid value retained
