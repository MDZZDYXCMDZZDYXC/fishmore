# fishmore

<img src="assets/icon-128.png" width="120" height="120" alt="fishmore icon">

A fishing-expansion plugin for the [Pumpkin](https://pumpkinmc.org) Minecraft server. On top
of the ordinary fishing loop, players can fish up **nearly every survival-mode item** — the
fish, junk and treasure that vanilla already gives you are untouched; the plugin only *adds*
a rare chance at a random extra item.

It changes nothing you can see or hear: no particles, no sounds, no chat messages. The only
difference a player notices is that their lines sometimes pull up something they could never
fish up before.

Built against the official Pumpkin plugin development guide
(`https://docs.pumpkinmc.org/plugin-dev/rust`) and compiled to a `wasm32-wasip2` component,
following the project layout of the reference plugin `two048`.

- Package / plugin name: `fishmore` v0.1.0 (Rust edition 2024)
- Artifact: `target/wasm32-wasip2/release/fishmore.wasm`
- Dependencies: `pumpkin-plugin-api = "0.2.0+26.3-26.51"`, `tracing`

## What it does

The plugin registers a single handler for the *player-fish* event and listens **only** for the
`caught-fish` state (the moment a bite is successfully reeled in). On that one state it rolls
once:

| Step | Detail |
| --- | --- |
| Trigger | `PlayerFishEventData.state == PlayerFishState::CaughtFish`, once per successful reel-in |
| Roll | `Rng::below(1200) == 0` — one chance in **1200** |
| Payoff | one item, count 1, chosen uniformly from the candidate pool |
| Delivery | placed into the player's inventory (stack onto a matching item first, then an empty slot) |

If the roll misses — which it does 1199 times out of 1200 — nothing at all happens. The vanilla
drop is produced by the server exactly as normal; the extra item is granted **in addition** to it.

There are no commands, no GUI, no configuration and no permissions to grant.

## Item pool

The candidate pool is derived from the API's own item registry, minus what vanilla fishing
already covers and minus what survival cannot obtain:

```
pool = ALL_ITEMS (1657)
     − VANILLA_CATCHABLE (20)
     − UNOBTAINABLE (21)
     − spawn eggs (88)
     = 1528 items
```

- **`ALL_ITEMS`** ([src/items.rs](src/items.rs)) is the complete registry, exported verbatim from
  `pumpkin-plugin-api`'s `Item` enum — the file is pure data and contains no filtering logic.
- **`VANILLA_CATCHABLE`** ([src/lib.rs](src/lib.rs)) — the 20 items vanilla already drops as fish,
  junk or treasure (cod, salmon, tropical fish, pufferfish; lily pad, bowl, leather, leather
  boots, rotten flesh, stick, string, bone, ink sac, tripwire hook; bow, enchanted book, fishing
  rod, name tag, nautilus shell, saddle). These are left to the vanilla loot logic, so the
  "extra" pool never duplicates them.
- **`UNOBTAINABLE`** ([src/lib.rs](src/lib.rs)) — 21 items that cannot be obtained in survival:
  - technical / developer blocks and items: `air`, `debug_stick`, `light`, `structure_void`,
    `structure_block`, `jigsaw`, `test_block`, `test_instance_block`;
  - the command-block family (they require operator permission): `command_block`,
    `chain_command_block`, `repeating_command_block`, `command_block_minecart`;
  - blocks that survival cannot obtain: `bedrock`, `barrier`, `spawner`, `trial_spawner`,
    `vault`, `end_portal_frame`, `reinforced_deepslate`, `budding_amethyst`, `knowledge_book`.
- **spawn eggs** — every `*_spawn_egg` item is excluded by suffix (creative-only, and they would
  let a player spawn hostile mobs).

Obtainable edge cases are deliberately **kept**: `dragon_egg`, `netherite_block`, `cobweb`,
`farmland`, `dirt_path`, `suspicious_sand`, `suspicious_gravel`, chipped/damaged anvils, and so
on. The rule of thumb is "can it be obtained in survival?" — if yes, it is in the pool.

## Balance

The extra-item chance is pinned to a vanilla reference point so it stays genuinely rare:

```rust
/// The vanilla chance of fishing up an enchanted book (5% treasure / 6 entries ≈ 1/120).
const ENCHANTED_BOOK_ONE_IN: u64 = 120;
/// The extra item is one tenth of that ≈ 1/1200.
const EXTRA_ONE_IN: u64 = ENCHANTED_BOOK_ONE_IN * 10;
```

So the extra item is **one tenth as likely as a vanilla enchanted book**, and always a single
count — a rare bonus on top of the normal catch, never a replacement for it.

## Why it works this way

`pumpkin-plugin-api = "0.2.0+26.3-26.51"` currently offers no way to:

- read or rewrite the item stack of the entity that was just fished up (`entity` has no item-stack
  accessor);
- spawn an `item` entity carrying a specific stack (`world` can spawn by `entity-type` only);
- change the output of loot generation (`loot-generate-event` exposes only the table name).

The one mechanism left — and the one that does not disturb vanilla drops — is to hand the item
straight to the player's inventory when the catch is confirmed. That is what the plugin does.

## Permissions

None. The plugin neither reads nor writes files, uses the network, or touches any host capability,
so its `PluginMetadata.permissions` list is empty. The event handler is registered with
`EventPriority::Normal` and `blocking = false`, because it never modifies the event.

## Requirements

- A Pumpkin server whose plugin API matches the pinned crate version
  (`pumpkin-plugin-api = "0.2.0+26.3-26.51"`).
- To build from source: a Rust toolchain with the `wasm32-wasip2` target.

```sh
rustup target add wasm32-wasip2
```

## Building and installing

`.cargo/config.toml` already pins `wasm32-wasip2` as the default build target, and the
`[profile.release]` block enables LTO, so a plain build produces the plugin:

```sh
cargo build --release
```

Then copy the artifact into the server's plugin directory and restart:

```sh
cp target/wasm32-wasip2/release/fishmore.wasm /path/to/server/plugins/
```

There is nothing to enable afterwards — the plugin is passive and starts working the next time
somebody casts a line.

## Project layout

```
src/
  lib.rs        Plugin entry point: metadata, event registration, the fish handler,
                the RNG, and the inventory-insertion helper
  items.rs      The full item registry (data only, 1657 names)
assets/
  make_icon.py  Icon generator (writes icon.svg; also renders the PNGs when Pillow is installed)
  icon.svg      Vector icon source
  icon-64/128/256/512.png
                Rasterised icons, used by this README and the repository listing
```

## Implementation notes

- All gameplay rules — which items are excluded and how rare the bonus is — live in a handful of
  named constants in [src/lib.rs](src/lib.rs) (`VANILLA_CATCHABLE`, `UNOBTAINABLE`,
  `ENCHANTED_BOOK_ONE_IN`, `EXTRA_ONE_IN`), which keeps them auditable in one place.
- There is no `rand` dependency. Randomness comes from the same `splitmix64` generator used by the
  reference plugin, seeded by mixing a host-provided random UUID with the wall clock — which
  sidesteps the missing `getrandom` backend under `wasm32-wasip2`.
- `Plugin::on_load` takes `&self`, and the handler takes no locks at all, so the "never hold a
  non-reentrant lock across a host call" rule that the Pumpkin docs warn about is satisfied by
  construction. The `uuid` host call happens before any state is touched.
- The candidate pool is recomputed on each hit rather than cached. Since the code only reaches
  that path about once in 1200 catches, the cost of filtering ~1657 names is irrelevant.

## Testing

`cargo test` is not usable for this crate: `crate-type` is `cdylib` and `.cargo/config.toml` pins
the `wasm32-wasip2` target, so no test binary can run on the host. The plugin is therefore
verified with a clean `cargo build --release` and an empty `cargo clippy --release` (the same
approach as `two048`), plus a check that the generated `fishmore.wasm` exports `init-plugin` and
`get-metadata`.

The item pool arithmetic above was checked against the generated registry: 1657 total, with
`bedrock` / `barrier` / `spawner` / `trial_spawner` / `vault` / `end_portal_frame` /
`reinforced_deepslate` / `budding_amethyst` / `knowledge_book` confirmed absent from the pool and
`dragon_egg` / `netherite_block` / `cobweb` / `dirt_path` / `suspicious_sand` confirmed present.

## Troubleshooting

**Fishing behaves exactly like vanilla.** Either the roll simply missed (1199 times out of 1200),
or your server build does not dispatch the *player-fish* event. The plugin registers the handler
correctly against the API, but whether the host fires the event is up to the server implementation.

**Cargo prints a warning about semver metadata.** `pumpkin-plugin-api = "0.2.0+26.3-26.51"`
carries build metadata after the `+`, which Cargo ignores for version resolution and warns about.
It is harmless, and the version is pinned deliberately so that `cargo update` cannot silently move
the plugin onto an API track your server does not implement.

## Credits

Project layout, RNG and command/event wiring follow the reference plugin `two048` and the official
Pumpkin plugin development guide. Plugin API signatures were verified against the
`pumpkin-plugin-api` WIT definitions rather than the guide's snippets, which have drifted in places.
