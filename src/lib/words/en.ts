// Generated from the en catalog by design-catalogs. Do not edit.

import type { Words } from "./de.js";
// prettier-ignore
const translated = {
    "signIn.loggedOut": "You are logged out.",
    "signIn.logIn": "Log in",
    "signIn.loginFailed": "Login failed",
    "signIn.loginFailedBanner": "Sign-in did not work. Please try again.",
    "signIn.tryAgain": "Try again",
    "signIn.noAccess": "No access",
    "signIn.noAccessSentence": (gaps: { readonly appName: string }) => "You are signed in, but this account has no access to " + gaps.appName + ".",
    "signIn.logOut": "Log out",
    "signIn.signingIn": "Signing in",
    "signIn.inOtherWindow": "In the other window",
    "signIn.openInTab": "Open in a tab",
    "signIn.windowBlocked": "Window blocked",
    "signIn.windowBlockedSentence": "Your browser blocked the sign-in window.",
    "signIn.signInUnfinished": "Sign-in did not finish.",
    "account.theme": "Theme",
    "account.followSystem": "Follow system",
    "account.light": "Light",
    "account.dark": "Dark",
    "account.logOut": "Log out",
    "agent.call": "Call",
    "agent.calling": "Calling…",
    "agent.askToLeave": "Ask to leave",
    "agent.callLabel": (gaps: { readonly name: string }) => "Call " + gaps.name,
    "agent.askToLeaveLabel": (gaps: { readonly name: string }) => "Ask " + gaps.name + " to leave",
    "agent.empty": "No agent is reachable right now.",
    "agent.notAllowed": "You may not call this agent.",
    "agent.ownerAbsent": "Its owner is not here.",
    "agent.placeFull": "There is no room here for another agent.",
    "agent.agentUnavailable": "The agent is not reachable right now.",
    "agent.tryAgain": "That did not work. Please try again.",
    "legalLinks.name": "Legal",
} satisfies Words;
// A translation that leaves out a gap of its source fails here.
({} as Words) satisfies typeof translated;
export const words: Words = translated;
