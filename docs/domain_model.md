# RabbitFarm Domain Model

## Core Entities

### Rabbit
Individual animal with unique number.
Used for breeding or sale animals.

### Litter
Result of kindling from one doe.
Represents newborn rabbits before weaning.

### YoungGroup
Group of young rabbits after weaning.
Managed as production unit.

### Event
Any farm action or biological event.
Creates farm history.

---

## Lifecycle

Pairing
→ Kindling (creates Litter)
→ Weaning (creates YoungGroup)
→ Sex Split
→ Selection
→ Individual Rabbits or Fattening Group
