import os
import torch
import torch.nn as nn
from torch.nn import functional as F

from src.rwkv7.Channel_mix import RWKV_CMix_x070
from src.rwkv7.Time_mix import RWKV_Tmix_x070

class Block(nn.Module):
        def __init__(self, args, layer_id):
            super().__init__()
            self.args = args
            self.layer_id = layer_id

            self.ln1 = nn.LayerNorm(args.n_embd)
            self.ln2 = nn.LayerNorm(args.n_embd)

            if self.layer_id == 0:
                self.ln0 = nn.LayerNorm(args.n_embd)

            self.att = RWKV_Tmix_x070(args, layer_id)  
            self.ffn = RWKV_CMix_x070(args, layer_id)


        def forward(self, x, v_first):
            if self.layer_id == 0:
                x = self.ln0(x)

            x_attn, v_first = self.att(self.ln1(x), v_first)
            x = x + x_attn

            x = x + self.ffn(self.ln2(x))
            return x, v_first
        
class block(nn.Module):
        def __init__(self, args, layer_id):
            super().__init__()
            self.args = args
            self.layer_id = layer_id

            self.ln_att = nn.LayerNorm(args.n_embd)
            self.ln_ffn = nn.LayerNorm(args.n_embd)


            self.att = RWKV_Tmix_x070(args, layer_id)  
            self.ffn = RWKV_CMix_x070(args, layer_id)


        def forward(self, x, v_first):

            x_attn, v_first = self.att(self.ln_att(x), v_first)
            x = x + x_attn

            x = x + self.ffn(self.ln_ffn(x))
            return x, v_first