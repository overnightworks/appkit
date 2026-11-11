# design vision

design is the shared toolbox of a family of web apps. It holds the parts every
app needs, so that no app builds them again and a change made once reaches all
of them.

## Why it exists, and for whom

Left alone, every app rebuilds the same things: its look, its sign-in page, its
account menu. The copies drift apart and a fix is made once per app. design
keeps one copy of each shared thing, so the family looks and reads as one
product and stays that way. It serves the people who build the apps: they take
what is shared and write only what is their own, which is data, rules and an
accent colour. The people who use the apps notice only that everything feels
familiar.

## What it can do

- Give every app the same look: colours, type, and a light and a dark theme that
  follows the device unless a person chooses.
- Make signing in look and read the same in every app, with the same wording
  for signed out, refused and failed.
- Offer the same account menu everywhere: who is signed in, the theme choice,
  signing out and the legal links.
- Let each app keep its own colour and words while the shared parts stay shared.
- Keep every app's words, and the shared parts' words, in one place per language, and catch a missing or outdated translation before it ships, so that a further language means adding its texts, not changing the app's code.
- Carry one change to every app: an app takes the new version when its builders
  choose, and a breaking change is announced openly.

A part joins design when an app needs it and stays only if it holds in every
app. Nothing is built ahead of use.

## What it is not

- Not an all-in package that arrives complete before anyone asks.
- Not a home for an app's data, rules or page layout.
- Not a place for service settings or secrets.
- Not a service: it runs nothing and is only taken in by the apps.

How it is built is in [ARCHITECTURE.md](ARCHITECTURE.md).
