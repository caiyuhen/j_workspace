def build_xgb_model(seed: int):
    from sklearn.ensemble import GradientBoostingClassifier

    return GradientBoostingClassifier(
        random_state=seed,
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
    )
