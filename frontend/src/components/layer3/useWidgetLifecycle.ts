/**
 * Re-export from WidgetLifecycleContext — single import path for widget authors.
 *
 * Usage inside a widget component:
 *   import { useWidgetLifecycle } from "@/components/layer3/useWidgetLifecycle";
 *
 *   function MyWidget({ data }) {
 *     useWidgetLifecycle({
 *       onMount: () => console.log("mounted"),
 *       onResize: (w, h) => console.log(`resized to ${w}x${h}`),
 *       onDataUpdate: (d) => console.log("data updated", d),
 *       onUnmount: () => console.log("cleanup"),
 *     });
 *     return <div>...</div>;
 *   }
 */
export { useWidgetLifecycle, WidgetLifecycleProvider } from "./WidgetLifecycleContext";
