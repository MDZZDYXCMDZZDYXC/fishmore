//! # fishmore — Pumpkin 服务器「钓鱼扩充」插件
//!
//! 在原版钓鱼的基础之上，让玩家几乎可以把**生存模式下的所有物品**都钓上来。
//!
//! ## 设计目标
//!
//! * 保留原版钓鱼的一切行为（鱼类、垃圾、宝藏的掉落逻辑完全不变）；
//! * 不改动任何特效、音效与界面，做到「体感原生」——玩家只是在拉竿时，
//!   偶尔会额外获得一件原本钓不到的物品；
//! * 为平衡起见，这些「额外物品」出现得极少：其概率被设定为
//!   **原版钓到附魔书概率的十分之一**（约 1/1200），命中后再从候选物品中随机取一件。
//!
//! ## 可钓取范围
//!
//! 「额外物品」的候选池 = **全部物品** − **原版本来就能钓到的物品** − **生存模式下无法获取的物品**：
//!
//! * 原版可获得物 [`VANILLA_CATCHABLE`]：鱼类 / 垃圾 / 宝藏，交由原版掉落逻辑负责，不重复发放；
//! * 生存不可获取物 [`UNOBTAINABLE`]：基岩、屏障、刷怪笼与试炼刷怪笼、宝库、
//!   末地传送门框架、强化深板岩、紫水晶母岩、知识之书，以及纯技术/开发方块
//!   （空气、光源方块、结构方块族、拼图方块、测试方块）与命令方块族；
//! * 创造专属的刷怪蛋（`*_spawn_egg`）。
//!
//! 其余物品（绝大多数方块与物品）都在候选池内。
//!
//! ## 实现方式与 API 限制
//!
//! Pumpkin 插件 API（`pumpkin-plugin-api = "0.2.0+26.3-26.51"`）目前**没有**提供
//! 「读取/修改已钓上来的物品实体」以及「向世界投放指定物品实体」的接口：
//!
//! * `entity` 资源没有物品堆访问器；
//! * `world` 无法「带物品地生成一个 item 实体」；
//! * `loot-generate-event` 只暴露 `loot-table` 名称，没有产出物品列表。
//!
//! 因此这里采用**唯一可行且不破坏原版掉落**的方案：监听玩家的
//! *player-fish* 事件，在「成功钓到（`caught-fish`）」这一状态上投一次骰子，
//! 命中则直接把随机物品**放入玩家背包**（先尝试堆叠，再找空格）。
//! 原版掉落照常发生，二者互不干扰。
//!
//! ## 插件权限
//!
//! 不使用文件、网络等宿主能力，因此不申请任何插件级权限。

use pumpkin_plugin_api::events::{EventPriority, EventHandler, PlayerFishEvent};
use pumpkin_plugin_api::inventory::Inventory;
use pumpkin_plugin_api::wit::pumpkin::plugin::event::{PlayerFishEventData, PlayerFishState};
use pumpkin_plugin_api::{
    Context, ItemStack, ItemStackExt, Plugin, PluginMetadata, Server, register_plugin,
};

mod items;

/// 原版钓鱼中「附魔书」的大致概率。
///
/// 原版钓鱼的掉落分为鱼类（85%）/ 垃圾（10%）/ 宝藏（5%）三类；宝藏类共有
/// 6 种物品（弓、附魔书、钓鱼竿、命名牌、鹦鹉螺壳、鞍）等权随机，
/// 于是附魔书的概率约为 `5% / 6 ≈ 1/120`。
const ENCHANTED_BOOK_ONE_IN: u64 = 120;

/// 「额外物品」的出现频率：附魔书概率的十分之一，约 `1/1200`。
const EXTRA_ONE_IN: u64 = ENCHANTED_BOOK_ONE_IN * 10;

/// 原版本来就能钓到的物品（鱼类 / 垃圾 / 宝藏）。
///
/// 这些物品不属于「额外」范畴——它们由原版掉落逻辑负责，本插件不再重复发放，
/// 从而保证「除了本来就可以钓的物品外，其它物品概率都很小」这一平衡设定。
const VANILLA_CATCHABLE: &[&str] = &[
    // 鱼类
    "cod",
    "salmon",
    "tropical_fish",
    "pufferfish",
    // 垃圾
    "lily_pad",
    "bowl",
    "leather",
    "leather_boots",
    "rotten_flesh",
    "stick",
    "string",
    "bone",
    "ink_sac",
    "tripwire_hook",
    // 宝藏
    "bow",
    "enchanted_book",
    "fishing_rod",
    "name_tag",
    "nautilus_shell",
    "saddle",
];

/// 生存模式下**无法获取**的物品，一律不进入钓鱼随机池。
///
/// 分三类：纯技术/开发方块与物品、命令方块族（需管理员权限），以及原版生存里
/// 拿不到的方块。刷怪蛋另由 [`is_spawn_egg`] 按后缀排除。
const UNOBTAINABLE: &[&str] = &[
    // 纯技术 / 开发用（无实际生存用途，或根本不可放置）
    "air",
    "debug_stick",
    "light",
    "structure_void",
    "structure_block",
    "jigsaw",
    "test_block",
    "test_instance_block",
    // 命令方块族：使用需要管理员权限
    "command_block",
    "chain_command_block",
    "repeating_command_block",
    "command_block_minecart",
    // 生存模式下无法获取的方块
    "bedrock",
    "barrier",
    "spawner",
    "trial_spawner",
    "vault",
    "end_portal_frame",
    "reinforced_deepslate",
    "budding_amethyst",
    "knowledge_book",
];

/// 刷怪蛋属于创造专属物品，且可用于刷出敌对生物，因此整体排除。
fn is_spawn_egg(name: &str) -> bool {
    name.ends_with("_spawn_egg")
}

/// 插件本体。
struct Fishmore;

impl Plugin for Fishmore {
    fn new() -> Self {
        Fishmore
    }

    fn metadata(&self) -> PluginMetadata {
        PluginMetadata {
            name: "fishmore".into(),
            version: env!("CARGO_PKG_VERSION").into(),
            authors: vec!["WorkBuddy".into()],
            description:
                "让钓鱼能钓上几乎所有生存物品，额外物品极稀有 · Fish up nearly every item, very rarely"
                    .into(),
            dependencies: Vec::new(),
            // 不读写文件、不联网，无需申请任何宿主权限。
            permissions: Vec::new(),
        }
    }

    fn on_load(&self, context: Context) -> pumpkin_plugin_api::Result<()> {
        // 钓到物品（caught-fish）时投骰子；不改动事件本身，因此不阻塞。
        context.register_event_handler(FishHandler, EventPriority::Normal, false)?;

        tracing::info!(
            "fishmore 已加载：原版钓鱼不变，额外物品约 1/{EXTRA_ONE_IN} 概率入包（候选 {} 种，已排除生存不可获取与刷怪蛋）",
            extra_pool().len()
        );
        Ok(())
    }
}

register_plugin!(Fishmore);

// ---------------------------------------------------------------------------
// 事件：玩家钓到东西
// ---------------------------------------------------------------------------

/// 玩家钓鱼事件处理器。
///
/// 只在 `caught-fish` 状态触发——`fishing`、`bite`、`reel-in` 等中间状态一律忽略，
/// 因此每次成功拉竿最多只会判定一次。
struct FishHandler;

impl EventHandler<PlayerFishEvent> for FishHandler {
    fn handle(&self, _server: Server, data: PlayerFishEventData) -> PlayerFishEventData {
        if !matches!(data.state, PlayerFishState::CaughtFish) {
            return data;
        }

        // 随机源会调用宿主接口（uuid::generate），此处未持有任何锁，安全。
        let mut rng = Rng::new();
        if rng.below(EXTRA_ONE_IN as usize) != 0 {
            return data;
        }

        let pool = extra_pool();
        if pool.is_empty() {
            return data;
        }
        let name = pool[rng.below(pool.len())];

        let inv = data.player.get_inventory().as_inventory();
        if !give_to_inventory(&inv, ItemStack::of(name, 1)) {
            // 背包已满：本次额外物品作废，但原版掉落不受影响。
            tracing::debug!("fishmore: {} 的背包已满，额外物品 {name} 未能发放", data.player.get_name());
        }

        data
    }
}

/// 全部「额外物品」候选：从全部物品中剔除
/// **原版本来就能钓到的**（[`VANILLA_CATCHABLE`]）与**生存不可获取的**
/// （[`UNOBTAINABLE`] 及刷怪蛋）两类。
///
/// 每次调用都重新过滤一遍。由于只有约 1/1200 的命中率才会走到这里，
/// 这点纯计算的代价可以忽略，无需额外的缓存与初始化顺序假设。
fn extra_pool() -> Vec<&'static str> {
    items::ALL_ITEMS
        .iter()
        .copied()
        .filter(|name| !VANILLA_CATCHABLE.contains(name))
        .filter(|name| !UNOBTAINABLE.contains(name) && !is_spawn_egg(name))
        .collect()
}

/// 把一份物品放进背包：先尝试堆叠到同类物品上，否则找一个空槽位。
///
/// 成功返回 `true`；背包放不下返回 `false`。
fn give_to_inventory(inv: &Inventory, stack: ItemStack) -> bool {
    let key = stack.get_registry_key();
    let add = u32::from(stack.get_count());

    for slot in 0..inv.get_size() {
        if let Some(existing) = inv.get_item(slot)
            && existing.get_registry_key() == key
        {
            let max = u32::from(existing.get_max_count());
            let cur = u32::from(existing.get_count());
            if cur + add <= max {
                existing.set_count(u8::try_from(cur + add).unwrap_or(u8::MAX));
                inv.set_item(slot, Some(existing));
                return true;
            }
        }
    }

    for slot in 0..inv.get_size() {
        if inv.get_item(slot).is_none() {
            inv.set_item(slot, Some(stack));
            return true;
        }
    }
    false
}

// ---------------------------------------------------------------------------
// 伪随机数：uuid + 时间混合播种的 splitmix64
// ---------------------------------------------------------------------------

/// 与 `two048` 同款的确定性随机源：不引入 `rand`，也就绕开了
/// `wasm32-wasip2` 下没有 `getrandom` 后端的问题。
struct Rng {
    state: u64,
}

impl Rng {
    fn new() -> Self {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map_or(0, |d| d.as_nanos() as u64);
        let uid = pumpkin_plugin_api::uuid::generate();
        Self {
            state: now ^ uid.high ^ uid.low.rotate_left(32) ^ 0x9E37_79B9_7F4A_7C15,
        }
    }

    /// splitmix64：每调用一次推进一步，返回质量良好的 64 位随机数。
    fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    /// 返回 `[0, bound)` 内的下标；`bound == 0` 时返回 0。
    fn below(&mut self, bound: usize) -> usize {
        if bound == 0 {
            0
        } else {
            (self.next_u64() % bound as u64) as usize
        }
    }
}
