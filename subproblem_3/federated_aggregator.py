"""
federated_aggregator.py

Lightweight FedAvg simulation used to build a per-role "peer baseline"
tensor so brand-new users can be scored immediately instead of waiting
to accumulate personal history.

Component 1 of Sub-Problem 3.2 (Federated Cold-Start).
"""

from __future__ import annotations

from typing import List

import torch


class FederatedPeerAggregator:
    """
    Aggregates stable users' embeddings into a single per-role global
    tensor via Federated Averaging (FedAvg):

        w_global = (1/N) * sum_{i=1}^{N} w_i

    In production, w_i is computed once per "stable" user (>50
    historical logs) by running SecurityHGNN.get_user_embedding() on
    that user's own local baseline graph. Only the resulting embedding
    vector -- never the raw logs themselves -- needs to be shared with
    the aggregator; this is what makes the scheme privacy-preserving.
    """

    def aggregate_peer_weights(self, role: str, peer_embeddings: List[torch.Tensor]) -> torch.Tensor:
        """
        Args:
            role: job role, e.g. "MARKETING" (kept for logging /
                cache-keying by the caller).
            peer_embeddings: list of N tensors, each shape
                [embedding_dim], one per stable user sharing `role`.

        Returns:
            w_global: Tensor[embedding_dim] -- the FedAvg-aggregated
            peer baseline for `role`.

        Raises:
            ValueError: if peer_embeddings is empty or the embeddings
                have mismatched shapes.
        """
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
        """
        Per-dimension standard deviation across the peer group. Feeds
        ColdStartEvaluator's 3-sigma boundary check.

        Returns:
            Tensor[embedding_dim]
        """
        if len(peer_embeddings) < 2:
            # Std is undefined for N<2; fall back to unit variance so
            # downstream z-scores degrade gracefully instead of NaN-ing.
            dim = peer_embeddings[0].shape[0] if peer_embeddings else 0
            return torch.ones(dim)
        stacked = torch.stack(peer_embeddings, dim=0)  # [N, embedding_dim]
        return stacked.std(dim=0, unbiased=True)        # [embedding_dim]
