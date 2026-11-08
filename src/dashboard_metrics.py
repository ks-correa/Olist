"""Reloj de reproducción y fotografía de estado; independientes de Streamlit."""
from dataclasses import dataclass
import numpy as np

SPEEDS=(1,6,24,72,168)


@dataclass
class PlayerState:
    index: int=0
    playing: bool=False
    speed: int=24
    last_tick: float | None=None
    credit: float=0.
    window: str='principal'
    scenario: str='E0'

    def context(self,window,scenario):
        if window!=self.window:
            self.seek(0);self.window=window
        if scenario!=self.scenario:
            self.pause();self.scenario=scenario

    def seek(self,index):
        if isinstance(index,bool) or not isinstance(index,(int,np.integer)) or index<0:
            raise ValueError('Índice temporal inválido')
        self.index=int(index);self.playing=False;self.last_tick=None;self.credit=0.

    def play(self,now,maximum):
        if self.index<maximum:
            self.playing=True;self.last_tick=now

    def pause(self):
        self.playing=False;self.last_tick=None;self.credit=0.

    def tick(self,now,maximum):
        if maximum<0 or self.index>maximum:
            raise ValueError('Índice fuera de la ventana')
        if self.playing and self.last_tick is not None:
            elapsed=max(0.,now-self.last_tick)
            self.last_tick=now;self.credit+=elapsed*self.speed
            steps=int(self.credit);self.credit-=steps
            self.index=min(maximum,self.index+steps)
            if self.index==maximum:
                self.pause()
        return self.index

    def set_speed(self,speed,now,maximum):
        if speed not in SPEEDS:
            raise ValueError('Velocidad no disponible')
        self.tick(now,maximum);self.speed=int(speed)


def snapshot(series,index,cumulative_purchases=None):
    if isinstance(index,bool) or not isinstance(index,(int,np.integer)) or not 0<=index<=series.duration:
        raise ValueError('Índice fuera de la trayectoria')
    levels=series.states[index].copy()
    purchases=series.cumulative_purchases if cumulative_purchases is None else cumulative_purchases
    incoming=None if index==0 else np.r_[series.purchases[index-1],series.flows[index-1]]
    flows=None if index==0 else series.flows[index-1].copy()
    expected=float(series.states[0].sum()+purchases[index])
    return {'index':int(index),'date':np.datetime_as_string(series.dates[index],unit='m').replace('T',' '),
        'levels':levels,'delta':None if index==0 else levels-series.states[index-1],
        'flows':flows,'incoming':incoming,'purchases':float(purchases[index]),
        'pending':float(levels[:3].sum()),'deliveries':float(levels[3]-series.states[0,3]),
        'conservation':float(levels.sum()-expected),'area':float(series.area[index])}
