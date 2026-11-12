// Generated from the de catalog by design-catalogs. Do not edit.

export const language = "de";
// prettier-ignore
export type Words = {
    readonly "signIn.loggedOut": string;
    readonly "signIn.logIn": string;
    readonly "signIn.loginFailed": string;
    readonly "signIn.loginFailedBanner": string;
    readonly "signIn.tryAgain": string;
    readonly "signIn.noAccess": string;
    readonly "signIn.noAccessSentence": (gaps: { readonly appName: string }) => string;
    readonly "signIn.logOut": string;
    readonly "signIn.signingIn": string;
    readonly "signIn.inOtherWindow": string;
    readonly "signIn.openInTab": string;
    readonly "signIn.windowBlocked": string;
    readonly "signIn.windowBlockedSentence": string;
    readonly "signIn.signInUnfinished": string;
    readonly "account.theme": string;
    readonly "account.followSystem": string;
    readonly "account.light": string;
    readonly "account.dark": string;
    readonly "account.logOut": string;
    readonly "agent.call": string;
    readonly "agent.calling": string;
    readonly "agent.askToLeave": string;
    readonly "agent.callLabel": (gaps: { readonly name: string }) => string;
    readonly "agent.askToLeaveLabel": (gaps: { readonly name: string }) => string;
    readonly "agent.empty": string;
    readonly "agent.notAllowed": string;
    readonly "agent.ownerAbsent": string;
    readonly "agent.placeFull": string;
    readonly "agent.agentUnavailable": string;
    readonly "agent.tryAgain": string;
    readonly "hearing.agentMayHearMe": string;
    readonly "hearing.iWantToHearAgent": string;
    readonly "legalLinks.name": string;
};
// prettier-ignore
export const words: Words = {
    "signIn.loggedOut": "Du bist abgemeldet.",
    "signIn.logIn": "Anmelden",
    "signIn.loginFailed": "Anmeldung fehlgeschlagen",
    "signIn.loginFailedBanner": "Die Anmeldung hat nicht geklappt. Bitte versuch es noch einmal.",
    "signIn.tryAgain": "Erneut versuchen",
    "signIn.noAccess": "Kein Zugang",
    "signIn.noAccessSentence": (gaps: { readonly appName: string }) => "Du bist angemeldet, aber dieses Konto hat keinen Zugang zu " + gaps.appName + ".",
    "signIn.logOut": "Abmelden",
    "signIn.signingIn": "Anmeldung läuft",
    "signIn.inOtherWindow": "Im anderen Fenster",
    "signIn.openInTab": "In einem Tab öffnen",
    "signIn.windowBlocked": "Fenster blockiert",
    "signIn.windowBlockedSentence": "Dein Browser hat das Anmeldefenster blockiert.",
    "signIn.signInUnfinished": "Die Anmeldung wurde nicht abgeschlossen.",
    "account.theme": "Darstellung",
    "account.followSystem": "System",
    "account.light": "Hell",
    "account.dark": "Dunkel",
    "account.logOut": "Abmelden",
    "agent.call": "Rufen",
    "agent.calling": "Wird gerufen…",
    "agent.askToLeave": "Bitten zu gehen",
    "agent.callLabel": (gaps: { readonly name: string }) => gaps.name + " rufen",
    "agent.askToLeaveLabel": (gaps: { readonly name: string }) => gaps.name + " bitten zu gehen",
    "agent.empty": "Gerade ist kein Agent erreichbar.",
    "agent.notAllowed": "Du darfst diesen Agenten nicht rufen.",
    "agent.ownerAbsent": "Sein Besitzer ist nicht hier.",
    "agent.placeFull": "Hier ist kein Platz für einen weiteren Agenten.",
    "agent.agentUnavailable": "Der Agent ist gerade nicht erreichbar.",
    "agent.tryAgain": "Das hat nicht geklappt. Versuch es noch einmal.",
    "hearing.agentMayHearMe": "Agent darf mich hören",
    "hearing.iWantToHearAgent": "Ich will den Agenten hören",
    "legalLinks.name": "Rechtliches",
};
export type Key = keyof Words;
