## MODIFIED Requirements

### Requirement: The shop drain runs on the same schedule as the availability drain and before it

The scheduled drain SHALL run the shop drain and the availability drain on each pass, at start-up and on the configured interval, under the conditions that already govern the scheduler — the enabling switch, not `STUB_MODE`, and a configured feed. The shop drain MUST run **before** the availability drain within a pass. Neither drain may block process start-up, and a failure of either MUST NOT prevent the other from being attempted nor raise out of the scheduled task. The bounded retry the start-up drain performs MUST be applied to **each drain separately**: a drain that has already run MUST NOT be repeated, and one drain succeeding MUST NOT end the retry of the other. When the attempts run out the service MUST record which of the two never ran.

**The order is a correctness rule and not a preference.** The count this capability reports crosses both tables. With the shops drained first, the only transient state is *shops known, assortment not yet written*, which the count correctly reports as points of sale lacking an assortment — a true statement for as long as it lasts. With the order reversed the transient state is *assortment written, no shop known*, in which the count has nothing to count against and reports an environment as complete while it is not. One order produces a truthful alarm that clears itself; the other produces a silent pass.

**Retrying per drain rather than per pass is the half that was missing, and a deployment paid for it.** Keyed on the pass as a whole, the start-up drain ended its retry as soon as *either* drain returned a result. On 2026-09-27 the shop drain failed by **1.2 seconds** — the business API was not yet serving its feed — while the availability drain, one second later, succeeded; the loop returned, and the shop table stayed empty until the interval tick ten minutes later, long past the window post-deployment verification waits through. The verification failed the deployment, correctly, and the environment cured itself on that tick. It is the same defect this capability exists to close, one level up: *part of the work succeeded* read as *the work succeeded*. The start-up drain is the only place where this matters, because it is the only moment at which nothing else will fill the gap in time.

#### Scenario: Both drains run at start-up in order

- **GIVEN** a service starting with the scheduler enabled and a configured feed
- **WHEN** the start-up pass runs
- **THEN** the shop drain runs before the availability drain
- **AND** `GET /health` answers throughout

#### Scenario: The start-up retry continues for the drain that has not run

- **GIVEN** a service starting while the business API is not yet serving its feed
- **AND** the shop drain fails on the first attempt while the availability drain succeeds on it
- **WHEN** the start-up drain retries
- **THEN** the shop drain is attempted again
- **AND** the availability drain is not repeated
- **AND** both tables are current before the retries are exhausted

#### Scenario: Exhausted retries record which drain never ran

- **GIVEN** a start-up drain whose attempts are exhausted with one drain still not run
- **WHEN** it gives up to the interval
- **THEN** the record states, per drain, whether it ran

#### Scenario: A failing shop drain does not stop the availability drain

- **GIVEN** the shop feed is unreachable
- **WHEN** a scheduled pass runs
- **THEN** the failure is logged
- **AND** the availability drain is still attempted
- **AND** no exception escapes the scheduled task

#### Scenario: The scheduler stays off under stub mode

- **GIVEN** `STUB_MODE` is enabled
- **WHEN** the service starts
- **THEN** neither drain is scheduled
