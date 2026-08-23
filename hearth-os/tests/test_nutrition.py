from app.services.nutrition import PLACEHOLDER_KG, person_need


def test_unknown_weight_uses_placeholder_and_says_estimate():
    need = person_need(weight_kg=None, cancer_track=True)
    assert need.weight_kg == PLACEHOLDER_KG
    assert need.weight_known is False
    assert need.estimate is True
    assert "estimate" in need.label
    assert "weight unknown" in need.label
    assert need.protein_g == round(1.2 * 70.0, 1)
    assert need.kcal == round(25.0 * 70.0, 1)


def test_known_weight_cancer_floor():
    need = person_need(weight_kg=80.0, cancer_track=True, protein_target_g=50, kcal_target=1000)
    assert need.protein_g == round(1.2 * 80.0, 1)
    assert need.kcal == round(25.0 * 80.0, 1)
    assert need.weight_known is True


def test_soft_food_does_not_change_floors():
    a = person_need(weight_kg=70.0, cancer_track=True, soft_food=False)
    b = person_need(weight_kg=70.0, cancer_track=True, soft_food=True)
    assert a.protein_g == b.protein_g
    assert a.kcal == b.kcal
