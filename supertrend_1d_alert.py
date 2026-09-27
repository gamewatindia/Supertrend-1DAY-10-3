import os
import time
import requests
import pandas as pd
import ccxt

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

TIMEFRAME = "1d"
ATR_PERIOD = 10
ATR_MULTIPLIER = 3.0

# Priority: WEEX -> Binance -> Bybit -> OKX -> Bitget
EXCHANGE_PRIORITY = ["weex", "binance", "bybit", "okx", "bitget"]

# Only these coins can ever be scanned.
ALLOWED_COINS = {
    x.strip().upper()
    for x in """
BTC
ETH
SOL
XRP
DOGE
1000PEPE
1000SHIB
Orca
Alch
Bless
Esp
Solv
Space
1mbabydoge
1000bonk
Bas
Manta
Wlfi
Rsr
Xtz
Bera
Goat
Kaito
Cat
Pendle
Ake
Gmt
Rave
Ray
Auction
Bluai
Xpl
Wif
Cgpt
Meta
Meme
Pump
Lpt
Mew
Fartcoin
Ar
Imx
Chip
Polyx
River
Glm
Flow
Skhynix
1000sats
Arc
Ava
Cetus
Gas
Sand
Apt
Ena
Crv
Linea
Arkm
Jellyjelly
Zrx
Evaa
Xaut
TRX
Moca
Aster
Hype
Kaia
Atom
Cheems
S
W
Light
Xny
Mina
Link
Kite
Tst
Coin
Chillguy
Usual
Act
Awe
Cyber
Cl
Xmr
Sapien
Avnt
Bz
VVV
Skl
Rez
Red
People
Xag
At
Cookie
Clo
Pha
Baba
Siren
Lit
Zk
Ltc
Aztec
Wal
Folks
Inj
Flux
Jasmy
Fil
Dym
1000floki
Og
Op
Vana
Lumia
Nmr
Alt
Hbar
Aave
Ape
Uai
Pnut
Xan
Giggle
Celo
Prom
Sei
Lab
Tao
Xau
G
Velodrome
Zora
Hmstr
Axs
Googl
Lyn
Rare
Not
Plume
Uni
Bard
Nil
Spk
Sqd
Tut
Spell
Xpd
Trump
Bio
Amd
Bmt
Hana
Cys
Dram
Coti
Merl
Form
Somi
Koma
Sndk
Samsung
Xvg
Aero
Move
Band
Pltr
Trb
Mmt
Xlm
Moodeng
Virtual
Vet
Lista
Pengu
Jct
Etc
Cati
Hood
Melania
Kas
Soxl
Vtho
Grass
Natgas
Enso
Banana
Zen
2z
Morpho
Rvn
Tsla
Swarms
Render
Zec
Mon
Xpt
Arb
Dash
Skyai
Tia
Mu
B2
Mstr
Msft
Pyth
Koru
Xai
Myx
Intc
Irys
Zil
Neo
Tnsr
Mubarak
Fet
Nvda
AMZN
Bat
Ta
Pons
Soon
Crcl
Dood
Dexe
Anime
Marscoin
Spcx
Bnb
Trust
Flock
Pol
Turtle
Ens
Dogs
Turbo
Resolv
Avax
Sto
Cbrs
Wld
Near
H
Dot
Gala
Jup
Magic
Gua
1000000mog
Spx
Sahara
Zro
Cake
Strk
Theta
Comp
Akt
Cow
Rune
Enj
Ldo
Useless
Eigen
Ban
Allo
Paxg
Mavia
Recall
Prompt
Bome
Tlm
Pixel
Ada
Popcat
ICP
Syn
Mask
Saga
1000rats
Stbl
Beat
Take
Esports
Met
Ethfi
Cfx
Ondo
Fhe
Io
Pippin
Fida
Pieverse
Bananas31
Wct
Snx
Sui
Tradoor
Br
Dia
Agld
Coai
Algo
4
Parti
Neirocto
Egld
Santos
Brett
Ordi
M
Aevo
Kgen
Xpin
Api3
Drift
Yb
Apr
Ub
Hemi
Bb
Bch
Jto
Grt
The
Eul
Mito
Zerebro
Aixbt
Wmt
Griffain
Ace
Safe
""".splitlines()
    if x.strip()
}


def create_exchange(exchange_id):
    try:
        cls = getattr(ccxt, exchange_id)

        return cls({
            "enableRateLimit": True,
            "timeout": 30000,
            "options": {
                "defaultType": "swap"
            }
        })

    except Exception as e:
        print(
            f"{exchange_id.upper()} init error: {e}"
        )
        return None


EXCHANGES = {
    eid: ex
    for eid in EXCHANGE_PRIORITY
    if (ex := create_exchange(eid)) is not None
}


def get_symbols(exchange_id, exchange):

    print(
        f"Loading {exchange_id.upper()} markets..."
    )

    try:
        markets = exchange.load_markets()

    except Exception as e:
        print(
            f"{exchange_id.upper()} market error: {e}"
        )
        return {}

    result = {}

    for symbol, market in markets.items():

        try:

            # Only perpetual / swap
            if not market.get("swap"):
                continue

            # Only linear contracts
            if market.get("linear") is False:
                continue

            # Only USDT settled
            if (
                str(
                    market.get("settle") or ""
                ).upper()
                != "USDT"
            ):
                continue

            # Skip inactive
            if market.get("active") is False:
                continue

            base = str(
                market.get("base") or ""
            ).upper()

            # Only our allowlist
            if base not in ALLOWED_COINS:
                continue

            if base not in result:
                result[base] = symbol

        except Exception:
            continue

    print(
        f"{exchange_id.upper()}: "
        f"{len(result)} allowed coins"
    )

    return result


def build_market_map():

    maps = {
        eid: get_symbols(
            eid,
            EXCHANGES[eid]
        )
        for eid in EXCHANGE_PRIORITY
        if eid in EXCHANGES
    }

    selected = {}

    for coin in sorted(ALLOWED_COINS):

        for eid in EXCHANGE_PRIORITY:

            if coin in maps.get(eid, {}):

                selected[coin] = {
                    "exchange_id": eid,
                    "symbol": maps[eid][coin]
                }

                break

    print("")
    print("=" * 70)
    print("FINAL MARKET SELECTION")
    print("=" * 70)

    print(
        f"Requested : {len(ALLOWED_COINS)}"
    )

    print(
        f"Selected  : {len(selected)}"
    )

    print(
        f"Missing   : "
        f"{len(ALLOWED_COINS) - len(selected)}"
    )

    counts = {
        eid: 0
        for eid in EXCHANGE_PRIORITY
    }

    for data in selected.values():

        counts[
            data["exchange_id"]
        ] += 1

    print("")
    print("Exchange distribution:")

    for eid in EXCHANGE_PRIORITY:

        print(
            f"  {eid.upper():8} : "
            f"{counts[eid]}"
        )

    print("")
    print("Selected markets:")

    for coin in sorted(selected):

        data = selected[coin]

        print(
            f"  {coin:15} -> "
            f"{data['exchange_id'].upper():8} "
            f"{data['symbol']}"
        )

    missing = sorted(
        ALLOWED_COINS
        -
        set(selected)
    )

    if missing:

        print("")
        print(
            "Unavailable on all supported exchanges:"
        )

        print(
            ", ".join(missing)
        )

    print("")

    return selected


def send_telegram(message):

    if not BOT_TOKEN or not CHAT_ID:

        print(
            "BOT_TOKEN / CHAT_ID missing."
        )

        return False

    url = (
        "https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    try:

        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=20
        )

        if response.ok:

            print(
                "Telegram alert sent."
            )

            return True

        print(
            "Telegram error:",
            response.status_code,
            response.text
        )

    except Exception as e:

        print(
            "Telegram connection error:",
            e
        )

    return False


def rma(
    series,
    period
):

    out = pd.Series(
        index=series.index,
        dtype=float
    )

    if len(series) < period:
        return out

    out.iloc[
        period - 1
    ] = series.iloc[
        :period
    ].mean()

    alpha = 1.0 / period

    for i in range(
        period,
        len(series)
    ):

        out.iloc[i] = (
            out.iloc[i - 1]
            +
            alpha
            *
            (
                series.iloc[i]
                -
                out.iloc[i - 1]
            )
        )

    return out


def supertrend(
    df,
    period=10,
    multiplier=3.0
):

    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,

            (
                high - prev_close
            ).abs(),

            (
                low - prev_close
            ).abs()
        ],
        axis=1
    ).max(axis=1)

    atr = rma(
        tr,
        period
    )

    hl2 = (
        high + low
    ) / 2.0

    upper = (
        hl2
        +
        multiplier * atr
    )

    lower = (
        hl2
        -
        multiplier * atr
    )

    final_upper = pd.Series(
        index=df.index,
        dtype=float
    )

    final_lower = pd.Series(
        index=df.index,
        dtype=float
    )

    direction = pd.Series(
        index=df.index,
        dtype=int
    )

    st = pd.Series(
        index=df.index,
        dtype=float
    )

    for i in range(
        len(df)
    ):

        if pd.isna(
            atr.iloc[i]
        ):

            final_upper.iloc[i] = (
                upper.iloc[i]
            )

            final_lower.iloc[i] = (
                lower.iloc[i]
            )

            direction.iloc[i] = 1

            st.iloc[i] = (
                upper.iloc[i]
            )

            continue

        if i == period - 1:

            final_upper.iloc[i] = (
                upper.iloc[i]
            )

            final_lower.iloc[i] = (
                lower.iloc[i]
            )

            direction.iloc[i] = 1

            st.iloc[i] = (
                upper.iloc[i]
            )

            continue

        previous_upper = (
            final_upper.iloc[i - 1]
        )

        previous_lower = (
            final_lower.iloc[i - 1]
        )

        if (
            lower.iloc[i]
            >
            previous_lower
            or
            close.iloc[i - 1]
            <
            previous_lower
        ):

            final_lower.iloc[i] = (
                lower.iloc[i]
            )

        else:

            final_lower.iloc[i] = (
                previous_lower
            )

        if (
            upper.iloc[i]
            <
            previous_upper
            or
            close.iloc[i - 1]
            >
            previous_upper
        ):

            final_upper.iloc[i] = (
                upper.iloc[i]
            )

        else:

            final_upper.iloc[i] = (
                previous_upper
            )

        previous_direction = (
            direction.iloc[i - 1]
        )

        if previous_direction == 1:

            if (
                close.iloc[i]
                >
                final_upper.iloc[i]
            ):

                direction.iloc[i] = -1

            else:

                direction.iloc[i] = 1

        else:

            if (
                close.iloc[i]
                <
                final_lower.iloc[i]
            ):

                direction.iloc[i] = 1

            else:

                direction.iloc[i] = -1

        if direction.iloc[i] == -1:

            st.iloc[i] = (
                final_lower.iloc[i]
            )

        else:

            st.iloc[i] = (
                final_upper.iloc[i]
            )

    return (
        direction,
        st
    )


def check_symbol(
    coin,
    data
):

    exchange_id = data[
        "exchange_id"
    ]

    symbol = data[
        "symbol"
    ]

    exchange = EXCHANGES[
        exchange_id
    ]

    try:

        ohlcv = exchange.fetch_ohlcv(
            symbol,
            timeframe=TIMEFRAME,
            limit=200
        )

    except Exception as e:

        print(
            f"{coin} | "
            f"{exchange_id.upper()} "
            f"OHLCV error: {e}"
        )

        return None

    if (
        not ohlcv
        or
        len(ohlcv) < 50
    ):

        print(
            f"{coin}: "
            f"insufficient candle data"
        )

        return None

    df = pd.DataFrame(
        ohlcv,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    # -2 = latest closed candle
    # -3 = previous closed candle

    previous_candle = -3
    confirmed_candle = -2

    direction, st = supertrend(
        df,
        ATR_PERIOD,
        ATR_MULTIPLIER
    )

    previous_close = float(
        df["close"].iloc[
            previous_candle
        ]
    )

    confirmed_close = float(
        df["close"].iloc[
            confirmed_candle
        ]
    )

    previous_st = float(
        st.iloc[
            previous_candle
        ]
    )

    confirmed_st = float(
        st.iloc[
            confirmed_candle
        ]
    )

    if (
        pd.isna(previous_st)
        or
        pd.isna(confirmed_st)
    ):

        return None

    previous_direction = int(
        direction.iloc[
            previous_candle
        ]
    )

    confirmed_direction = int(
        direction.iloc[
            confirmed_candle
        ]
    )

    buy_signal = (
        previous_close <= previous_st
        and
        confirmed_close > confirmed_st
        and
        confirmed_direction == -1
    )

    sell_signal = (
        previous_close >= previous_st
        and
        confirmed_close < confirmed_st
        and
        confirmed_direction == 1
    )

    print(
        f"{coin} | "
        f"{exchange_id.upper()} | "
        f"PrevClose={previous_close:.10f} | "
        f"PrevST={previous_st:.10f} | "
        f"ConfirmClose={confirmed_close:.10f} | "
        f"ConfirmST={confirmed_st:.10f} | "
        f"Direction="
        f"{previous_direction}"
        f"->{confirmed_direction}"
    )

    if (
        not buy_signal
        and
        not sell_signal
    ):

        return None

    if buy_signal:

        signal = (
            "🟢 BUY SIGNAL"
        )

        trend = "UP"

    else:

        signal = (
            "🔴 SELL SIGNAL"
        )

        trend = "DOWN"

    timestamp = int(
        df["timestamp"].iloc[
            confirmed_candle
        ]
    )

    candle_time = pd.to_datetime(
        timestamp,
        unit="ms",
        utc=True
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    message = (
        f"{signal}\n\n"
        f"Coin: {coin}\n"
        f"Exchange: "
        f"{exchange_id.upper()} Futures\n"
        f"Symbol: {symbol}\n"
        f"Timeframe: 1D\n"
        f"Supertrend: 10/3\n\n"
        f"Closed Candle: {candle_time}\n"
        f"Close Price: {confirmed_close}\n"
        f"Trend: {trend}\n\n"
        f"Supertrend crossover "
        f"confirmed on closed candle."
    )

    print("")
    print(
        "=" * 70
    )

    print(message)

    print(
        "=" * 70
    )

    print("")

    return message


def main():

    print("")

    print(
        "=" * 70
    )

    print(
        "MULTI-EXCHANGE FUTURES "
        "SUPERTREND 1D SCANNER"
    )

    print(
        "=" * 70
    )

    print(
        "Priority    : "
        "WEEX -> Binance -> Bybit -> OKX -> Bitget"
    )

    print(
        "Market      : USDT Perpetual"
    )

    print(
        "Timeframe   : 1D"
    )

    print(
        "Supertrend  : 10/3"
    )

    print(
        "Confirmation: CLOSED CANDLE"
    )

    print(
        "=" * 70
    )

    print("")

    try:

        selected = (
            build_market_map()
        )

    except Exception as e:

        print(
            "Unable to build market map:",
            e
        )

        return

    if not selected:

        print(
            "No allowed coins found."
        )

        return

    signals = 0

    for coin in sorted(
        selected
    ):

        try:

            message = check_symbol(
                coin,
                selected[coin]
            )

            if message:

                signals += 1

                send_telegram(
                    message
                )

        except Exception as e:

            print(
                f"{coin} "
                f"scanner error: {e}"
            )

        time.sleep(
            0.15
        )

    print("")

    print(
        "=" * 70
    )

    print(
        f"SCAN COMPLETE | "
        f"Signals: {signals}"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()