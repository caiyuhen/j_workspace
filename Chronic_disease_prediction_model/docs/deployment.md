# 部署手册

## 环境准备
- Python 3.10+
- CPU环境即可

## 本地部署
```
pip install -r requirements.txt
python api/app.py
```

## Docker部署
```
docker build -t chronic-risk .
docker run -p 5008:5008 chronic-risk
```

## 模型训练
```
python scripts/generate_synth_data.py
python scripts/train.py --data_path data_raw_synthetic.csv --output_dir models
```
