"""UI cleanup registry — optional control groups hideable from Settings.

Tabs register their 'nice-to-have but not workflow-critical' component
groups here; the Settings tab renders one toggle per group.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import gradio as gr

GROUPS: Dict[str, Tuple[gr.components.Component, str]] = {}
# name -> (component, human label)


def register(name: str, component: gr.components.Component, label: str) -> None:
    GROUPS[name] = (component, label)


def names() -> List[str]:
    return list(GROUPS.keys())


def label_of(name: str) -> str:
    return GROUPS[name][1]


def toggle(name: str, visible: bool):
    comp, _ = GROUPS[name]
    return gr.update(visible=bool(visible))
