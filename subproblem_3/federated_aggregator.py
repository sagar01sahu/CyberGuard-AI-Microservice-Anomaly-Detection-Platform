

from __future__ import annotations

from typing import List

import torch


class FederatedPeerAggregator:


    def aggregate_peer_weights(self, role: str, peer_embeddings: List[torch.Tensor]) -> torch.Tensor:

        if not peer_embeddings:
            raise ValueError(f"No peer embeddings available to aggregate for role='{role}'.")

        expected_shape = peer_embeddings[0].shape
        for i, emb in enumerate(peer_embeddings):
            if emb.shape != expected_shape:
                raise ValueError(
                    f"Peer embedding {i} has shape {tuple(emb.shape)}, "
                    f"expected {tuple(expected_shape)}."
                )

        stacked = torch.stack(peer_embeddings, dim=0)  # [N, embedding_dim]
        w_global = stacked.mean(dim=0)                 # [embedding_dim] == (1/N) * sum_i w_i
        return w_global

    def compute_peer_std(self, peer_embeddings: List[torch.Tensor]) -> torch.Tensor:

        if len(peer_embeddings) < 2:
            # Std is undefined for N<2; fall back to unit variance so
            # downstream z-scores degrade gracefully instead of NaN-ing.
            dim = peer_embeddings[0].shape[0] if peer_embeddings else 0
            return torch.ones(dim)
        stacked = torch.stack(peer_embeddings, dim=0)  # [N, embedding_dim]
        return stacked.std(dim=0, unbiased=True)        # [embedding_dim]
