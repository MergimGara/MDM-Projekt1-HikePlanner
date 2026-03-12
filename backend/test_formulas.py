from backend.formulas import din33466, sac, timedelta_minutes

def test_din33466():
    # Example: 10km, 300m up, 300m down
    # horizontal = 10 / 4 = 2.5h
    # vertical = 300/300 + 300/500 = 1.0 + 0.6 = 1.6h
    # Total = min(1.6, 2.5)/2 + max(1.6, 2.5) = 0.8 + 2.5 = 3.3h = 11880 seconds
    time_sec = din33466(uphill=300, downhill=300, distance=10000)
    assert abs(time_sec - 11880.0) < 1.0

def test_sac():
    # Example: 10km, 400m up, 0m down
    # horizontal = 10 / 4 = 2.5h
    # vertical = 400 / 400 = 1h
    # Total = 3.5h = 12600 seconds
    time_sec = sac(uphill=400, downhill=0, distance=10000)
    assert abs(time_sec - 12600.0) < 1.0

def test_timedelta_minutes():
    # 3600 seconds = 1:00:00
    assert timedelta_minutes(3600) == "1:00:00"
    # 3640 seconds = 60.66 minutes -> rounds to 61 minutes -> 1:01:00
    assert timedelta_minutes(3640) == "1:01:00"
    # 7200 seconds = 2:00:00
    assert timedelta_minutes(7200) == "2:00:00"
