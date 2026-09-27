"""Package « simulator » : simulateur Python d'un kit ESP32.

Utilisé pour développer et tester SANS le kit physique (§ cahier des
charges : développer avec le simulateur d'abord). Il publie sur le
broker MQTT exactement ce que fera l'ESP32 :
- un message de statut périodique  → {prefix}/kits/{kit}/status
- des mesures régulières           → {prefix}/kits/{kit}/telemetry

⚠️ Les valeurs générées sont SIMULÉES (balisées « simulated: true ») :
elles ne doivent jamais être présentées comme des mesures réelles.
"""
