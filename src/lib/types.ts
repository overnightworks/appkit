import type { Snippet } from 'svelte';
import type { Words as KitWords } from './words/de.ts';

/**
 * How a kit component logs out, in one of two forms.
 * With `onLogOut`, the button calls it and an optional `logOutFailure` text shows as an alert.
 * With `logOutAction`, a URL, the button submits a plain same-origin POST form to it: no script,
 * no token, no alert, so it works on a page prerendered with `csr = false`.
 */
export type LogOut =
	| { onLogOut: () => void; logOutFailure?: string; logOutAction?: never }
	| { logOutAction: string; onLogOut?: never; logOutFailure?: never };

/**
 * The five sign-in states: `signed-out` and `login-failed` link to `signInHref`
 * (`login-failed` adds a failure banner, as an alert); `no-access` logs out in either `LogOut` form,
 * or shows no log-out action when the app passes none (inside a call's frame).
 * `signed-out` may carry `onSignIn`, called by a plain click on "Log in" instead of following the link
 * (an app opens the sign-in in a separate window), and `unfinished`, which shows that a sign-in did not finish.
 * `signing-in` shows that the sign-in runs in the other window and links to `tabHref`, which opens the app in a tab.
 * `window-blocked` shows that the browser blocked that window and offers only the same link to `tabHref`.
 * Their words come from the kit's catalogs and are listed in docs/stylesheet.md.
 */
export type SignInState =
	| { page: 'signed-out'; signInHref: string; onSignIn?: () => void; unfinished?: true }
	| { page: 'signing-in'; tabHref: string }
	| { page: 'window-blocked'; tabHref: string }
	| ({ page: 'no-access' } & LogOut)
	| { page: 'no-access'; onLogOut?: never; logOutAction?: never; logOutFailure?: never }
	| { page: 'login-failed'; signInHref: string };

/** One entry of the legal row; the row keeps the given order and renders one link per entry, even when two share an href. */
export interface LegalLink {
	label: string;
	href: string;
}

/** `page` links open in the same tab unless `newTab` is set; `menu` is the row inside `AccountMenu`, whose links open in a new tab. */
export type LegalLinksPlace = 'page' | 'menu';

/**
 * Props of `LegalLinks`, a `<nav>` of the given links; an empty list renders nothing.
 * `words` names the row for assistive technology.
 * `newTab` opens a `page` row's links in a new tab with the same look.
 * The look comes from `design.css`, not from the component.
 */
export type LegalLinksProps =
	| { links: readonly LegalLink[]; words: KitWords; place?: 'page'; newTab?: boolean }
	| { links: readonly LegalLink[]; words: KitWords; place: 'menu'; newTab?: never };

/** The effective choice, never the resolved colour. */
export type ThemeChoice = 'follow-system' | 'light' | 'dark';

/**
 * The theme radios are controlled: the checked radio always equals `choice`,
 * so an app that does not take the reported pick sees the radio snap back.
 * The component stores nothing and writes no `data-theme`; the effective theme stays with the app.
 */
export interface ThemeRows {
	choice: ThemeChoice;
	/** Called only when a different radio is selected. */
	onChange: (choice: ThemeChoice) => void;
}

/** A row the app adds to the account panel, rendered above Theme. */
export interface AppRow {
	label: string;
	onSelect: () => void;
}

/**
 * The account panel: the name as a link to the account, the app's rows, an optional theme row,
 * the log-out button and the legal row. The kit owns the panel and its rows, which are taller
 * on a touch screen. It stores, fetches and closes nothing.
 */
export type AccountMenuProps = {
	/** The signed-in person's name; it keeps the case it was typed in. */
	name: string;
	/** The name links here and opens it in a new tab. */
	accountHref: string;
	/** The name link was activated. */
	onAccountOpen: () => void;
	/** Rendered above Theme; an empty list renders none. */
	appRows: readonly AppRow[];
	/** Absent renders no Theme row and writes nothing about the theme. */
	theme?: ThemeRows;
	/** An empty list shows no legal row. */
	legalLinks: readonly LegalLink[];
	/** The kit's words in the page's language, from `loadKitWords`. */
	words: KitWords;
} & LogOut;

/**
 * The sign-in page. The sign-in link carries `data-sveltekit-reload`, and the glow follows the theme.
 * It stores, fetches and closes nothing.
 */
export interface SignInPageProps {
	/** The page title. */
	appName: string;
	state: SignInState;
	/** An empty list shows no legal row. */
	legalLinks: readonly LegalLink[];
	/** Opens the legal row's links in a new tab, for a page shown inside another app's frame. */
	legalLinksNewTab?: boolean;
	/** The kit's words in the page's language, from `loadKitWords`. */
	words: KitWords;
}

/**
 * Why an agent's turns at a place do not answer, as the agents service states it (`StopOutcome`); apps
 * pass the stated value unchanged.
 */
export type TurnOutcome = 'not_enabled' | 'busy' | 'budget_spent' | 'unavailable';

/**
 * The mark and the kit's word for a stated turn outcome, meant to sit beside an agent's name. Without an
 * outcome it renders nothing. It holds no state and no timer: the app passes the last stated value and
 * drops it when the agent's seat ends.
 */
export interface TurnStateProps {
	outcome: TurnOutcome | undefined;
	/** The kit's words in the page's language, from `loadKitWords`. */
	words: KitWords;
}

/** How a call ended without a seat: the invitation ran out, the agent is busy, or its owner is away. */
export type AgentControlOutcome = 'no-answer' | 'busy' | 'owner-absent';

/**
 * One row of the agent control. `inviting` is a call under way, `here` an agent in the place and
 * `ended` a call that ended without a seat: the row shows its `outcome` in place of the waiting
 * text for a few seconds, then draws like an `available` row until the app changes it.
 */
export type AgentRow = {
	/** Opaque and minted by the app; the kit hands it back to `onCall` and `onSendAway`. */
	key: string;
	/** Shown as given. */
	name: string;
} & (
	| { state: 'available' | 'inviting' }
	| {
			state: 'here';
			/** The stated reason the agent's turns at the place do not answer; absent shows nothing extra. */
			turnState?: TurnOutcome;
	  }
	| { state: 'ended'; outcome: AgentControlOutcome }
);

/** Why a call or a send-away was refused; the same five reasons serve both actions. */
export type AgentControlRefusal =
	| 'not-allowed'
	| 'owner-absent'
	| 'place-full'
	| 'agent-unavailable'
	| 'try-again';

/**
 * The panel of rows with which a person calls an agent into a place and asks it to leave again:
 * each row leads with `AiMark`, then the name, then one action, the waiting text or the outcome of a
 * call. Trigger and popover stay with the app. The control holds no state of the call: the app sets
 * `rows` and `refusal` and clears them; its one timer only ends the display of an outcome. Asking to
 * leave takes effect at once, with no confirm step.
 */
export interface AgentControlProps {
	/**
	 * An empty list draws only the empty sentence, and the refusal when one is set. The sentence is
	 * `agent.placeFull` when `full` is set, `agent.empty` otherwise.
	 */
	rows: readonly AgentRow[];
	/**
	 * The place holds no further agent. With no rows, the empty sentence says so instead of saying
	 * that no agent is reachable. The app decides when the place is full; rows are drawn unchanged.
	 */
	full?: boolean;
	/** Called with the row's key by the button of an `available` row. */
	onCall: (key: string) => void;
	/**
	 * Called with the row's key by the button of a `here` row. Absent, a `here` row shows the mark and the
	 * name and no action, as an `inviting` row shows no button.
	 */
	onSendAway?: (key: string) => void;
	/** Its sentence shows above the rows as an alert until the app clears it. */
	refusal?: AgentControlRefusal;
	/** The kit's words in the page's language, from `loadKitWords`. */
	words: KitWords;
}

/** What the chip switches: the agent hears the person, the person hears the agent, or the agent sees the person. */
export type HearingKind = 'hear' | 'listen' | 'see';

/**
 * One chip with a switch for an agent's hearing, drawn on a video: `hear` is the agent hearing the
 * person ("Agent may hear me"), `listen` the person hearing the agent ("I want to hear the agent"),
 * `see` the agent seeing the person: its visible label is the short word "See" and its accessible name
 * the full "Agent may see me".
 * The chip holds no state: it shows `on` and, when pressed, calls `onChange` with the negated value;
 * the app sets `on` again or leaves it. The on colour is the app's `--accent`; the glass and the ink
 * are the chip's own. Where the chips stand and what a switch does stay with the app.
 */
export interface HearingSwitchProps {
	kind: HearingKind;
	/** Also the chip's `aria-checked`. */
	on: boolean;
	/** Called with the negated `on` by a press, Space or Enter. */
	onChange: (on: boolean) => void;
	/** The kit's words in the page's language, from `loadKitWords`. */
	words: KitWords;
	/**
	 * Draws only the 26 px track, the icon on its knob and the label visually hidden but still the
	 * accessible name, for a tile too narrow for the chip. Off by default; the app decides when it applies.
	 */
	compact?: boolean;
}

/**
 * The round ear that shows an agent hears a person, drawn on a video: the ear in a glass disc ringed in
 * the app's `--accent`, and the agent's name in a small pill beside it. It is one image whose name and
 * title read "<agent> hears you" on the person's own tile and "<agent> hears <person>" on another's.
 * The kit holds no state: the app mounts a mark only while the agent hears that person, stacks the marks
 * of several agents and places them on the tile.
 */
export interface EarMarkProps {
	/** The agent's name; shown in the pill and named in the accessible name. A long name ends in an ellipsis. */
	agent: string;
	/** The heard person's name on another person's tile; absent on one's own tile. */
	person?: string;
	/** The kit's words in the page's language, from `loadKitWords`. */
	words: KitWords;
}

/** One part of a marked sentence, as `design-catalogs` generates it: plain text, or text under a marker name. */
export type MarkedPart<Marker extends string> = string | { readonly marker: Marker; readonly text: string };

/**
 * Props of `Marked`, a marked sentence rendered in place, with no wrapper element and no white space of its own.
 * `parts` is the list a generated entry returns; the marker names are read from it.
 * `marked` holds one snippet per marker name, called with the part, so a page writes `{#snippet strong({ text }: { text: string })}`:
 * a parameter written as a plain name compiles to a default value that no call reaches, a branch an app measuring with istanbul counts.
 * The app chooses the element.
 * A missing snippet is a type error, and so is a snippet written in place for a name the sentence lacks.
 */
export interface MarkedProps<Marker extends string> {
	parts: readonly MarkedPart<Marker>[];
	marked: { [Name in NoInfer<Marker>]: Snippet<[{ readonly text: string }]> };
}

/** Who wrote a message of a helper conversation: the person or the helper agent. */
export type HelperRole = 'user' | 'assistant';

/** One tool the helper ran during a turn: its name and the input it ran with. */
export interface HelperToolCall {
	readonly name: string;
	readonly input: Readonly<Record<string, unknown>>;
}

/**
 * The part of a message that `HelperChat` renders. An app's own message type stays assignable to it
 * and passes through `HelperChat` unchanged to the snippets.
 */
export interface HelperMessage {
	readonly role: HelperRole;
	/** Already shaped by the app; shown as written, with line breaks kept. */
	readonly text: string;
	readonly toolCalls?: readonly HelperToolCall[];
}

/** Whether the conversation's earlier messages are there: `loading` and `failed` show instead of the list. */
export type HelperHistory =
	| { readonly state: 'ready' }
	| { readonly state: 'loading' }
	| { readonly state: 'failed'; readonly failure: string };

/**
 * The conversation a person has with an app's helper agent, drawn from props alone: the messages with
 * the helper's tool-call rows, the answer as it grows, the thinking line and the composer. The part holds
 * no fetch, no store and no app data, rules or page layout. The app places its header and notice before it
 * and owns the turn, the network and the scroll memory.
 *
 * The composer is controlled through `draft` and `onDraft`. Enter sends and Shift+Enter makes a new line;
 * a plain Enter is always cancelled, also while a turn runs, while the draft is empty and while the chat is
 * read-only, and nothing is sent during IME composition. `onComposerKeydown` runs first, and its
 * `preventDefault()` stops the send. The part's own colours come from `design.css` tokens and the app's
 * `--accent` and `--on-accent`.
 */
export interface HelperChatProps<Message extends HelperMessage> {
	messages: readonly Message[];
	/** A turn runs: the last helper message is the growing answer, and Send is off. */
	running: boolean;
	history: HelperHistory;
	/** The helper's name, the gap in the thinking line and in the composer's label. */
	helperName: string;
	/** Shown while the conversation is empty. */
	emptyHint: string;
	placeholder: string;
	/** The composer's text. */
	draft: string;
	/** Called with the field's text and its caret on every edit; the app sets `draft` again. */
	onDraft: (draft: string, caret: number) => void;
	/** Called with the trimmed draft, never empty, never while `running` or read-only. */
	onSend: (text: string) => void;
	/** Runs before the part handles the key; its `preventDefault()` stops the send. */
	onComposerKeydown?: (event: KeyboardEvent) => void;
	/** Present means read-only: a banner above the composer, and the composer disabled. */
	readOnly?: Snippet;
	/** The app's problem line, shown after the message it belongs to. */
	problemLine?: Snippet<[{ readonly message: Message; readonly index: number }]>;
	/** The target of a tool call, shown after its "ran tool" line. */
	toolCallTarget?: Snippet<[{ readonly call: HelperToolCall; readonly message: Message }]>;
	/** The title attribute of a tool-call row, such as the input as JSON. */
	toolCallTitle?: (call: HelperToolCall) => string;
	/** Inside the composer's box, above the field: a pick list. The box is `position: relative`. */
	composerPopup?: Snippet;
	/** Between the banner and the composer: a bar of tags. */
	composerTop?: Snippet;
	/** The message list's element, for the app's scroll memory. */
	list?: HTMLElement;
	/** Called when the message list scrolls. */
	onListScroll?: () => void;
	/** The kit's words in the page's language, from `loadKitWords`. */
	words: KitWords;
}
