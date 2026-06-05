import torch
from torch import nn


class TransformerClassifier(nn.Module):
    def __init__(self, input_dim: int, num_heads: int, hidden_dim: int, num_layers: int, output_dim: int):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.input_proj(x)
        encoded = self.encoder(x)
        pooled = encoded[:, -1, :]
        logits = self.fc(pooled)
        return torch.sigmoid(logits)
