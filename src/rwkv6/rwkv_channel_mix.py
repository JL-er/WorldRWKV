
import os, math, gc, importlib
import torch
import torch.nn as nn
from src.infctx_module import *
from src.rwkvLinear import make_linear_ffn

    
class RWKV_CMix_x060(nn.Module):
    def __init__(self, args, layer_id):
        super().__init__()
        self.args = args
        self.layer_id = layer_id
        self.time_shift = nn.ZeroPad2d((0, 0, 1, -1))

        with torch.no_grad():  # fancy init of time_mix
            ratio_1_to_almost0 = 1.0 - (layer_id / args.n_layer)  # 1 to ~0
            ddd = torch.ones(1, 1, args.n_embd)
            for i in range(args.n_embd):
                ddd[0, 0, i] = i / args.n_embd
            self.time_maa_k = nn.Parameter(1.0 - torch.pow(ddd, ratio_1_to_almost0))
            self.time_maa_r = nn.Parameter(1.0 - torch.pow(ddd, ratio_1_to_almost0))

        self.key = make_linear_ffn(args.n_embd, args.dim_ffn, bias=False)
        self.receptance = make_linear_ffn(args.n_embd, args.n_embd, bias=False)
        self.value = make_linear_ffn(args.dim_ffn, args.n_embd, bias=False)

    def forward(self, x):
        xx = self.time_shift(x) - x
        xk = x + xx * self.time_maa_k
        xr = x + xx * self.time_maa_r

        k = self.key(xk)
        k = torch.relu(k) ** 2
        kv = self.value(k)
        return torch.sigmoid(self.receptance(xr)) * kv

class RWKV_CMix_x060_infctx(nn.Module):
    def __init__(self, args, layer_id):
        super().__init__()
        self.args = args
        self.layer_id = layer_id
        self.time_shift = nn.ZeroPad2d((0, 0, 1, -1))

        with torch.no_grad():  # fancy init of time_mix
            ratio_1_to_almost0 = 1.0 - (layer_id / args.n_layer)  # 1 to ~0
            ddd = torch.ones(1, 1, args.n_embd)
            for i in range(args.n_embd):
                ddd[0, 0, i] = i / args.n_embd
            self.time_maa_k = nn.Parameter(1.0 - torch.pow(ddd, ratio_1_to_almost0))
            self.time_maa_r = nn.Parameter(1.0 - torch.pow(ddd, ratio_1_to_almost0))

        self.key = make_linear_ffn(args.n_embd, args.dim_ffn, bias=False)
        self.receptance = make_linear_ffn(args.n_embd, args.n_embd, bias=False)
        self.value = make_linear_ffn(args.dim_ffn, args.n_embd, bias=False)

    def forward(self, x, last_state: ChannelMixState):
        xx = torch.concat((last_state.shift_state.unsqueeze(1), x[:, :-1]), dim=1) - x
        xk = x + xx * self.time_maa_k
        xr = x + xx * self.time_maa_r

        k = self.key(xk)
        k = torch.relu(k) ** 2
        kv = self.value(k)
        return torch.sigmoid(self.receptance(xr)) * kv, ChannelMixState(x[:, -1])