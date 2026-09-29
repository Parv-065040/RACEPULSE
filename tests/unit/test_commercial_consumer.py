def test_fan_engagement_formula():
    viewers=50000
    interactions=6000+1000+500+250
    assert round(interactions/viewers,4)==0.155

def test_sponsor_conversion_is_zero_safe():
    clicks=0
    assert clicks/max(1,clicks)==0
