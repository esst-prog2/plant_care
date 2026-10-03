# HW4 spike: do the watering intervals match a citable source?

Question (GitHub issue #3): how many of the 41 bundled watering intervals in `data/plants.json`
disagree with a citable horticultural source (RHS or Kew), and what is the worst gap in days?

Method: 12 plants were picked to span the current spread of values in `data/plants.json`
(4, 5, 5, 7, 7, 7, 7, 10, 10, 14, 14, 21 days), each looked up directly on the RHS website
(rhs.org.uk) — the Royal Horticultural Society, a UK horticultural charity — or on Kew's public
site. All pages were fetched on 2026-10-02.

| Plant (our id) | Our value | Source URL | What the source says about watering | Gives a day-count? |
|---|---|---|---|---|
| Boston fern (`boston-fern`) | 4 days | https://www.rhs.org.uk/plants/11508/nephrolepis-exaltata/details | "During the growing season, water moderately with soft water... Water sparingly in winter." | No |
| Calathea (`calathea`) | 5 days | https://www.rhs.org.uk/plants/calathea/growing-guide | "Water plants moderately throughout spring and summer, keeping the compost evenly moist... Allow the surface of the compost to dry out before rewetting" in autumn/winter. | No |
| Prayer plant (`prayer-plant`) | 5 days | https://www.rhs.org.uk/plants/119598/maranta-leuconeura/details | "Water moderately, and feed monthly... Watering can be reduced in winter." | No |
| Monstera (`monstera`) | 7 days | https://www.rhs.org.uk/plants/11192/monstera-deliciosa-f/details | "Water when in growth and keep just moist in winter." | No |
| Pothos (`pothos`) | 7 days | https://www.rhs.org.uk/plants/epipremnum/growing-guide | "Only water once the compost is approaching dryness – test it with your finger first." | No |
| Peace lily (`peace-lily`) | 7 days | https://www.rhs.org.uk/plants/peace-lilies | "The roots can rot if the compost is damp for long periods, so take care not to overwater. Plants can droop dramatically when they need watering, but soon perk up after a good drink." | No |
| Spider plant (`spider-plant`) | 7 days | https://www.rhs.org.uk/plants/spider-plants/growing-guide | "Water regularly, aiming to keep the compost just lightly moist to the touch." | No |
| Snake plant (`snake-plant`) | 14 days | https://www.rhs.org.uk/plants/16430/sansevieria-trifasciata/details | "Protect from winter wet." "Tolerant of neglect." | No |
| Aloe vera (`aloe-vera`) | 14 days | https://www.rhs.org.uk/plants/aloe | Aloes "will not grow well in continuously wet compost." | No |
| Corn plant (`corn-plant`) | 10 days | https://www.rhs.org.uk/plants/dracaena/how-to-grow-dracaena | "Always check the compost before watering – only water once the top 5cm (2in) feels dry to the touch." | No |
| Christmas cactus (`christmas-cactus`) | 10 days | https://www.rhs.org.uk/plants/christmas-cactus/how-to-grow | "Water regularly from April to September, keeping the compost moist but never waterlogged," then reduce watering in the rest periods. | No |
| Cactus (`cactus`) | 21 days | https://www.rhs.org.uk/plants/types/cacti-succulents/houseplants/growing-guide | "Most indoor cacti and succulents should be watered thoroughly once the surface of the compost feels dry to the touch during spring and summer." | No |

Kew was also checked for two of these (Monstera, snake plant): Kew's public plant pages
(`powo.science.kew.org`) only carry taxonomic data — classification, native range, synonyms —
and no care or watering guidance at all, for either plant. Kew turned out not to be a usable
source for this question; everything above comes from the RHS.

## The answer

**0 of the 12** RHS pages state a watering interval as a number of days. Every one of them ties
watering to the state of the compost ("once the top 5cm feels dry", "once the compost is
approaching dryness") or to the season ("water moderately in spring/summer, sparingly in
winter"), never to a day count. So **the worst gap in days cannot be computed** — there is no
source figure to subtract our value from. The honest two-number answer is 0 out of 12 sources
give a comparable day figure, and 12 of 12 of our fixed-day values are therefore unverifiable
against the RHS, not merely approximately right or wrong.

**Decision:** stop calling `data/plants.json` care instructions. A single fixed number of days
can't be made to agree with a source that deliberately varies with season and with how fast a
particular pot dries out — citing a source per plant would mean inventing a day-count the source
itself never gives, which would be worse than labelling the number as a rough default. The app
now treats the interval as a starting point to check the plant by eye, not as a verified
schedule (see `README.md`, "Where the plant data comes from").
