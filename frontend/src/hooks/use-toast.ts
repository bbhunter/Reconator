import * as React from "react";

import type { ToastProps } from "@/components/ui/toast";

type ToasterToast = ToastProps & {
  id: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
};

const TOAST_LIMIT = 3;
const TOAST_REMOVE_DELAY = 4000;

type State = { toasts: ToasterToast[] };

type Action =
  | { type: "ADD"; toast: ToasterToast }
  | { type: "DISMISS"; id?: string }
  | { type: "REMOVE"; id?: string };

const listeners: Array<(s: State) => void> = [];
let memory: State = { toasts: [] };

function dispatch(action: Action) {
  memory = reducer(memory, action);
  listeners.forEach((l) => l(memory));
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "ADD":
      return { toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT) };
    case "DISMISS":
      return {
        toasts: state.toasts.map((t) =>
          action.id === undefined || t.id === action.id ? { ...t, open: false } : t,
        ),
      };
    case "REMOVE":
      return {
        toasts:
          action.id === undefined
            ? []
            : state.toasts.filter((t) => t.id !== action.id),
      };
  }
}

function genId() {
  return Math.random().toString(36).slice(2, 10);
}

export function toast(opts: Omit<ToasterToast, "id"> & { title?: React.ReactNode; description?: React.ReactNode }) {
  const id = genId();
  const t: ToasterToast = {
    ...opts,
    id,
    open: true,
    onOpenChange: (open) => {
      if (!open) dispatch({ type: "REMOVE", id });
    },
  };
  dispatch({ type: "ADD", toast: t });
  setTimeout(() => dispatch({ type: "REMOVE", id }), TOAST_REMOVE_DELAY);
  return id;
}

export function useToast() {
  const [state, setState] = React.useState<State>(memory);
  React.useEffect(() => {
    listeners.push(setState);
    return () => {
      const i = listeners.indexOf(setState);
      if (i > -1) listeners.splice(i, 1);
    };
  }, []);
  return {
    toasts: state.toasts,
    toast,
    dismiss: (id?: string) => dispatch({ type: "DISMISS", id }),
  };
}
