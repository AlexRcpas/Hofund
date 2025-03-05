# Hofund - Tower Defense Game

A tower defense shooting game where you play as Heimdall, the guardian of Asgard, defending against waves of monsters coming through wormholes.

## Game Description

The game screen is divided into three areas:
1. **Wormhole Area** (top 20% of the screen): Monsters spawn from this area and move downward.
2. **Attack Area** (middle 50% of the screen): Monsters travel through this area toward the defense line.
3. **Defense Area** (bottom 30% of the screen): Heimdall is positioned here and automatically shoots flying swords at the monsters.

## Game Mechanics

- Heimdall automatically shoots flying swords at monsters.
- Monsters spawn from the wormhole area and move downward.
- If monsters reach the defense line, they damage the armor.
- When armor reaches zero, the game is over.
- Out of the first 200 monsters, 20 will randomly drop upgrades when defeated.
- When you defeat a monster with an upgrade, a popup appears allowing you to choose one of the following upgrades:
  - Change sword type (Normal, Ice, Fire)
  - Add an additional sword
  - Increase fire rate
  - Increase damage range

## Sword Types

1. **Normal Sword**: Basic damage.
2. **Ice Sword**: Slows down monsters.
3. **Fire Sword**: Deals additional damage.

## How to Run the Game

1. Make sure you have Python installed (Python 3.6 or higher recommended).
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the game:
   ```
   python hofund.py
   ```

## Controls

- **Mouse Click**: Select upgrades when the upgrade popup appears.
- **R Key**: Restart the game after Game Over.

## Game Assets

The game uses the following assets from the `pic` directory:
- Hofund.png: Main character image
- Hofund0.jpeg: Alternative character image
- Heimdall00.jpeg: Character reference image

Enjoy defending Asgard! 