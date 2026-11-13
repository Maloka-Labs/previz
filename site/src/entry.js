/* Bundle entry (v2) — libs on window, then run the app. */
import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
window.Lenis = Lenis; window.gsap = gsap; window.ScrollTrigger = ScrollTrigger;
import "./main.js";
