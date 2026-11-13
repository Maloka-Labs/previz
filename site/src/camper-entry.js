/* Bundle entry (v2.5 camper) — libs on window, then run. */
import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
window.Lenis = Lenis; window.gsap = gsap; window.ScrollTrigger = ScrollTrigger;
import "./camper-main.js";
