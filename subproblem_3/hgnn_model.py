

from __future__ import annotations

from typing import Dict, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, SAGEConv

from graph_builder import (
    USER_FEAT_DIM,
    DEVICE_FEAT_DIM,
    LOCATION_FEAT_DIM,
    RESOURCE_FEAT_DIM,
)

EDGE_TYPES = [
    ("user", "logged_in_from", "device"),
    ("device", "rev_logged_in_from", "user"),
    ("user", "accessed", "resource"),
    ("resource", "rev_accessed", "user"),
    ("device", "located_in", "location"),
    ("location", "rev_located_in", "device"),
]

NODE_TYPES = ["user", "device", "location", "resource"]


class SecurityHGNN(nn.Module):


    def __init__(self, hidden_channels: int = 32, out_channels: int = 16) -> None:
        super().__init__()
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels

        in_channels = {
            "user": USER_FEAT_DIM,
            "device": DEVICE_FEAT_DIM,
            "location": LOCATION_FEAT_DIM,
            "resource": RESOURCE_FEAT_DIM,
        }

        # -- Layer 1: raw features [*, in_channels] -> [*, hidden_channels]
        conv1_dict = {}
        for edge_type in EDGE_TYPES:
            src, _, dst = edge_type
            conv1_dict[edge_type] = SAGEConv((in_channels[src], in_channels[dst]), hidden_channels)
        self.conv1 = HeteroConv(conv1_dict, aggr="mean")

        # -- Layer 2: [*, hidden_channels] -> [*, out_channels]
        conv2_dict = {}
        for edge_type in EDGE_TYPES:
            conv2_dict[edge_type] = SAGEConv((hidden_channels, hidden_channels), out_channels)
        self.conv2 = HeteroConv(conv2_dict, aggr="mean")

    def forward(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[Tuple[str, str, str], torch.Tensor],
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            x_dict: {node_type: Tensor[num_nodes_of_type, in_channels]}
            edge_index_dict: {edge_type: Tensor[2, num_edges]}

        Returns:
            {node_type: Tensor[num_nodes_of_type, out_channels]}
            Callers typically only need out_dict["user"],
            shape [num_users, out_channels].
        """
        h_dict = self.conv1(x_dict, edge_index_dict)
        h_dict = {k: F.relu(v) for k, v in h_dict.items()}


        for node_type in NODE_TYPES:
            if node_type not in h_dict and node_type in x_dict:
                h_dict[node_type] = torch.zeros(
                    x_dict[node_type].size(0), self.hidden_channels
                )

        out_dict = self.conv2(h_dict, edge_index_dict)
        out_dict = {k: F.relu(v) for k, v in out_dict.items()}

        for node_type in NODE_TYPES:
            if node_type not in out_dict and node_type in x_dict:
                out_dict[node_type] = torch.zeros(
                    x_dict[node_type].size(0), self.out_channels
                )
        return out_dict

    def get_user_embedding(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[Tuple[str, str, str], torch.Tensor],
    ) -> torch.Tensor:

        out_dict = self.forward(x_dict, edge_index_dict)
        user_emb = out_dict["user"]  # [num_users, out_channels]
        return user_emb.mean(dim=0)  # [out_channels]
