# book-factory v3 — Design Brief (contrato entre archivos)

Este documento es la ÚNICA fuente de verdad para la arquitectura v3. Todo archivo de la skill
debe ser consistente con lo que dice acá. Si un autor de archivo detecta un conflicto entre
este brief y otro archivo, gana el brief y el conflicto se reporta.

Contexto: v3 es un rediseño de la skill v2.4.3 (`C:\Users\seba_\.claude\skills\book-factory\`)
según la auditoría `docs/reviews/AUDITORIA-BOOK-FACTORY.md`.
Sin retrocompatibilidad: NO existen ramas de migración, NO se menciona v2 en los archivos
(salvo CHANGELOG.md). El idioma de la skill es inglés (como v2); la interacción con el humano
es en el idioma del usuario.

---

## 1. Decisiones de producto (no negociables)

1. **Perfiles de documento** reemplazan el binario literary/technical. Cinco perfiles:
   `book-technical`, `book-literary`, `corporate-guide`, `product-docs`, `scientific-paper`.
2. **Ejemplos GOOD por proyecto**: las references de la skill contienen SOLO reglas y ejemplos
   BAD (universales). Los ejemplos GOOD se generan en setup desde los calibration passages
   aprobados y viven en `bible/voice-profile.md` del proyecto. Ningún agente calibra contra
   ejemplos compartidos de la skill. Razón: los ejemplos GOOD globales de v2 crearon la
   "voz de fábrica" (ver auditoría P0-1).
3. **Perfil de voz por proyecto** (`bible/voice-profile.md`) + **presupuesto de retórica**
   (ítems contables del rubric). Ver §6 y §7.
4. **Rubric literario itemizado** con severidades (v2 era un stub).
5. **Paquete literario moderado**: friction inventory, exposition beats, pausa/pausing,
   secundarios con voz, cuota de riesgo de voz, Humanizer conservador, auditoría de
   singularidad cada 5 capítulos. Sin agentes nuevos.
6. **Pase adversarial opcional** post-Critic (`pipeline.adversarial_verify`).
7. **Fase 5 Build/Export** por perfil.
8. **Cost observability simplificada**: una línea por corrida de agente
   (`- [chapter, agent, model_tier, cycle, timestamp]`), sin tokens. v2 especificaba tokens
   que nadie poblaba.
9. **Modelos por tier**, no por ID: `models.tiers.creative` y `models.tiers.audit`, default
   `inherit` (modelo de la sesión). IDs explícitos solo si el humano quiere control de costos.
   PROHIBIDO hardcodear IDs de modelo en references o templates.

## 2. Árbol de archivos v3

```
book-factory.skill/
├── SKILL.md                      # mapa + phase detection + principios (lo escribe el lead)
├── CHANGELOG.md                  # historial fuera de SKILL.md
├── references/
│   ├── profiles/
│   │   ├── book-technical.md
│   │   ├── book-literary.md
│   │   ├── corporate-guide.md
│   │   ├── product-docs.md
│   │   └── scientific-paper.md
│   ├── setup.md                  # setup unificado profile-aware (incluye voice profile)
│   ├── knowledge-graph.md
│   ├── outlining.md              # profile-aware
│   ├── pipeline.md               # spec única del pipeline (ver §4)
│   ├── rubric.md                 # rubrics itemizados: nonfiction + literary + rhetoric budget
│   ├── validation-surface.md     # + citation_check y stats_check para papers
│   ├── adversarial-verify.md     # NUEVO
│   ├── build-export.md           # NUEVO (Fase 5)
│   ├── chapter-digest.md
│   ├── archiving.md
│   ├── loopback-handoff.md
│   ├── init-scaffold.md          # pregunta de perfil; sin migraciones
│   ├── anti-mediocrity-nonfiction.md   # reglas + ejemplos BAD only
│   ├── anti-mediocrity-literary.md     # reglas + ejemplos BAD only
│   └── agents/
│       ├── writer-nonfiction.md
│       ├── writer-literary.md
│       ├── technical-reviewer.md
│       ├── editor.md
│       ├── humanizer-nonfiction.md
│       ├── humanizer-literary.md
│       ├── reader-pov.md
│       ├── critic.md
│       ├── proofreader.md
│       └── continuity-guardian.md
└── templates/
    ├── meta.yaml                 # unificado, campo `profile`, tiers de modelo
    ├── voice-profile.md          # NUEVO
    ├── style-guide.md
    ├── project-status.yaml
    ├── scorecard.yaml            # NOMBRE CANÓNICO (no "critique-scorecard.yaml")
    ├── critique-report.md
    ├── chapter-entry.yaml
    ├── chapter-digest.md
    ├── sources.md
    ├── glossary.md
    ├── knowledge-graph.yaml
    ├── continuity-tracker.md
    ├── character-sheet.md
    ├── examples-library.md
    ├── claims-map.yaml           # NUEVO (scientific-paper)
    └── loopback-escalation.md
```

## 3. Estructura de proyecto generada (init)

```
project/
├── bible/
│   ├── meta.yaml                 # profile, audience, tone, structure, pipeline, models
│   ├── voice-profile.md          # huella de voz + ejemplos GOOD del proyecto + budgets
│   ├── style-guide.md            # decisiones de estilo + calibration passages
│   ├── glossary.md · scope.md · knowledge-graph.yaml · continuity-tracker.md
│   ├── sources/                  # grounding library (igual que v2: pdf + md + figures + sources.md)
│   ├── claims-map.yaml           # solo scientific-paper
│   ├── characters/ world.md plot-structure.md arcs.md timeline.md   # solo book-literary
│   ├── examples-library.md       # perfiles con running example
│   └── digests/                  # perfiles secuenciales only
├── outline/units.yaml            # "unit" = chapter|article|section según perfil
├── drafts/unit-NN/ · drafts/_archive/ · drafts/_polish/
├── final/unit-NN.md
├── project-status.yaml
├── manuscript.md                 # Fase 4 (perfiles secuenciales); product-docs NO concatena
└── build/                        # Fase 5 outputs (epub/pdf/docx/latex según perfil)
```

Nota terminología: internamente la unidad es "unit" para que product-docs (article) y
scientific-paper (section) no fuercen "chapter". Los perfiles book-* la llaman chapter en
la superficie. Los archivos usan `unit-NN`; los textos dirigidos al humano usan la palabra
del perfil.

## 4. Pipeline v3 (spec única — TODOS los archivos deben coincidir con esto)

### Nonfiction (book-technical, corporate-guide, product-docs, scientific-paper)

```
fast (default):
Writer → Technical Reviewer → Editor → Humanizer → Continuity Guardian (Mode A: coherence)
      → Critic (GATE) → [Adversarial Verify si está habilitado] → Human
      → (aprobado) Proofreader → Continuity Guardian (Mode B: tracker) → digest* → archive

full: igual + Reader-POV entre Humanizer y Continuity Guardian Mode A.
```

- El Critic SIEMPRE lee `humanized.md` (en fast y full). No hay excepciones.
- El Humanizer corre SIEMPRE por unidad (fast y full). El Editor NUNCA aplica fixes de prosa
  ni advisories del Reviewer (eso era deuda v2: duty duplicado). El Editor es estructural puro;
  los advisories del Reviewer los aplica el Humanizer.
- digest* solo en perfiles secuenciales (book-*, corporate-guide secuencial). product-docs no
  genera digests; scientific-paper genera un digest corto por sección (estado de claims).

### Literary (book-literary)

```
Writer → Editor → Humanizer → Reader-POV → Critic (GATE) → [Adversarial Verify] → Human
      → (aprobado) Proofreader → Continuity Guardian → digest → archive
```

### Verdictos y loopback (sin cambios de fondo vs v2, nombres canónicos)

- Technical Reviewer (nonfiction only): PASS | REVISE→Writer | ESCALATE.
- Critic: PASS | REVISE (target único) | REWORK (→Writer) | ESCALATE. Verdicto COMPUTADO del
  scorecard: 1 critical fail → REVISE; ≥2 critical → REWORK; ≥1 significant → REVISE;
  solo minor → PASS con notas (fast tolera minors; full: ≥3 minors → REVISE).
- retry_cap: fast 2, full 3, literary 3. Cap hit → paquete de escalación (loopback-handoff.md).
- Loopback por TIPO de problema: estructura→Editor; contenido/facts/framing→Writer;
  voz/prosa→Humanizer (ambos modos — el Humanizer existe siempre); confusión de lector→
  Reader-POV+Humanizer (full) o Writer (fast); beat de outline mal→ESCALATE.

### Adversarial Verify (nuevo, opcional)

- Config: `pipeline.adversarial_verify: off | gate_critical | every_unit | every_N` (default off;
  recomendado `every_N: 3` para proyectos largos).
- Tras un PASS del Critic: 3 skeptics en paralelo, CIEGOS al veredicto del Critic, cada uno con
  una lente distinta: (a) cumplimiento de perfil/registro, (b) corrección/grounding,
  (c) experiencia de lector. Mandato: REFUTAR el capítulo. Un hit confirmado por ≥2 → REVISE
  con el target que corresponda; hits de 1 → observaciones en el packet humano.
- Origen: en el proyecto Prompting un pase así (manual) cazó 2 veces problemas que el Critic
  había aprobado.

### Artefactos por unidad (nombres canónicos, NO variar)

`drafts/unit-NN/`: `grounding-notes.md` (nonfiction con sources), `draft.md`, `tech-review.md`
(nonfiction), `edit.md`, `humanized.md`, `reader-report.md` (full/literary), `coherence.md`
(Mode A), `critique.md`, `scorecard.yaml`, `adversarial-report.md` (si corre).

## 5. Sistema de perfiles

`bible/meta.yaml` declara `project.profile`. Cada perfil es UN archivo en
`references/profiles/` que TODOS los agentes cargan al inicio de su turno (es corto, <150
líneas). El perfil declara, con esta estructura común:

1. **Unit**: qué es la unidad (chapter/article/section) y cómo llamarla ante el humano.
2. **Sequence**: `linear | linear-light | modular | imrad`. Controla: digests on/off, KG
   obligatorio u opcional-terminología, forward-refs permitidos o prohibidos, orden de
   escritura. `linear-light` (corporate-guide) = secuencial pero cada unidad abre
   autocontenida y puede leerse salteada; digests livianos, sin promesas de lectura previa.
3. **Register**: defaults de registro y qué está PROHIBIDO. Ej. corporate-guide prohíbe
   mic-drops, auto-referencia ("this guide/book"), cliffhangers, cross-refs numeradas en
   prosa, promesas de transformación ("after this chapter you will be able to").
4. **Openings/closings policy**: estructuras permitidas de apertura (rotación obligatoria,
   ver §6) y política de cierre (recap | related-links | none | bridge-allowed).
5. **Citation policy**: `invisible` (HTML comments, como book-technical) o `visible-academic`
   (scientific-paper: citas formateadas en prosa + bibliografía). Esto INVIERTE reglas del
   Writer/Humanizer según perfil — el archivo del agente debe decir "según citation policy
   del perfil".
6. **Running example**: on/off/required.
7. **Rubric deltas**: ítems que se agregan/quitan/cambian de severidad para este perfil.
8. **Reader-POV persona(s)**: qué lector(es) simular. product-docs: usuario que aterriza por
   búsqueda con una tarea urgente. corporate-guide: empleado con 10 minutos. paper: reviewer 2
   escéptico + lector de abstract.
9. **Build targets** (Fase 5): book→EPUB/PDF/DOCX vía pandoc; corporate-guide→DOCX/PDF;
   product-docs→árbol markdown con frontmatter listo para SSG; paper→LaTeX/PDF con .bib.

### Notas por perfil

- **book-technical**: hereda el comportamiento v2 (grounding, KG, digests, ejercicios) +
  voice profile + rhetoric budget.
- **book-literary**: pipeline literario + paquete moderado (§8).
- **corporate-guide**: registro sobrio POR DEFECTO (las reglas que el usuario legisló a mano
  en el proyecto Prompting son el default del perfil). meta.yaml gana bloque
  `organization: {name, audience_role, internal_context, confidentiality}`. Secuencia
  linear-light (puede leerse salteado; cada unit abre autocontenida). Ejercicios → "practice"
  opcional con casos internos. Callouts: Note/Template/Checklist (no "Recipe").
- **product-docs**: unit=article, modular estricto. Sin manuscript.md (Fase 4 = auditoría de
  consistencia cross-article + índice). Sin digests. KG solo terminología. Frontmatter por
  article (title, description, tags, related). Prohibido asumir lectura previa: prerequisitos
  se LINKEAN. Aperturas: task-first ("This article shows how to X"). Sin ejercicios.
- **scientific-paper**: unit=section, sequence=imrad (orden de escritura: Methods→Results→
  Intro→Discussion→Abstract al final; el outline lo fija). Citas visibles: formato declarado
  en meta (`citation_style: apa|ieee|vancouver|author-year`). Artefacto nuevo
  `bible/claims-map.yaml`: cada claim del paper mapeado a evidencia (cita externa con fuente
  en `bible/sources/`, o resultado propio con referencia a datos). El Technical Reviewer gana
  **Axis C — Reference integrity**: la cita existe, dice lo que se le atribuye, no está
  retractada. Si hay MCPs de Zotero/citecheck/arxiv/openreview disponibles, usarlos para
  verificar; si no, verificación contra `bible/sources/` y flag de lo no verificable. Sección
  Limitations obligatoria (rubric critical). Methods con checklist de reproducibilidad.
  Validation surfaces típicas: `citation_check`, `stats_check`, `proof_recheck`, `python_exec`.

## 6. Voice profile (`bible/voice-profile.md`) — NUEVO artefacto por proyecto

Generado en setup (sub-fase obligatoria para todos los perfiles), plantilla en
`templates/voice-profile.md`. Contiene:

1. **Fingerprint**: 3-5 rasgos que ESTE autor/documento hace y otros no (ej: "abre con un
   dato numérico incómodo", "humor seco solo en callouts", "analogías solo del dominio X").
2. **Banned traits**: 3-5 rasgos prohibidos ADEMÁS del anti-mediocrity global.
3. **Opening rotation**: 3-4 estructuras de apertura permitidas, definidas por el humano en
   setup a partir de un menú (escena-problema / pregunta directa / dato contraintuitivo /
   caso del campo / task-first / in-media-res...). REGLA DURA: la misma estructura no puede
   usarse en dos unidades consecutivas. El Writer declara en su self-assessment cuál usó;
   el Critic lo verifica (rhet-6).
4. **Closing policy**: heredada del perfil, ajustable.
5. **Project GOOD examples**: 3-5 pasajes cortos en la voz del proyecto (los calibration
   passages + 1-2 ejemplos por técnica clave generados en setup y APROBADOS por el humano).
   Estos reemplazan a los ejemplos GOOD que v2 tenía en las references compartidas.
6. **Rhetoric budget overrides** (ver §7): el proyecto puede endurecer o aflojar los defaults.

Todos los agentes de prosa (Writer, Humanizer, Critic, CG Mode A) leen voice-profile.md
SIEMPRE, junto al style-guide.

## 7. Rhetoric budget (ítems de rubric contables — familia `rhet`)

Defaults (override en voice-profile.md). El Critic los cuenta con grep/conteo explícito y
reporta el número en evidence — no son vibes:

- `rhet-1` preguntas retóricas por unidad ≤ 2 — significant
- `rhet-2` construcciones "not X but Y" / "No es X, es Y" ≤ 1 — significant
- `rhet-3` léxico de peligro dramático ("silently", "invisible", "without complaint",
  "hidden danger" y equivalentes del idioma) ≤ 2 — significant
- `rhet-4` cliffhanger artificial al cierre = 0 cuando la closing policy es recap/none — significant
- `rhet-5` densidad de negritas ≤ 8 por 1000 palabras — minor
- `rhet-6` estructura de apertura ≠ la de la unidad anterior — significant
- `rhet-7` headings-plantilla ("What's next", "Payoff") solo cuando están ganados; si el
  contenido de la sección es vacío/formulaico, fail — minor

## 8. Paquete literario moderado (en writer-literary, editor, humanizer-literary, rubric, outlining)

1. **Friction inventory** (Writer, pre-draft): por cada escena de 300+ palabras declara en un
   bloque al inicio del self-assessment: qué quiere el POV / qué se opone / dónde pivota.
   Escena sin inventario = flag del Critic (`craft-5`, significant).
2. **Exposition beats** (outlining): el outline marca beats como `scene` o
   `exposition-within-scene`; los segundos llevan instrucción de "accionar la información"
   (no diálogo informativo puro).
3. **Pausa vs pausing** (Editor + rubric): beats de pausa requieren interrupción o cambio de
   estado interno, no solo anclas sensoriales (`craft-2`, significant).
4. **Secundarios** (outlining + rubric): personaje que aparece 2+ veces necesita ≥1 línea
   propia (`craft-3`, minor; significant si reincide entre unidades).
5. **Cuota de riesgo de voz** (Writer): 1 riesgo deliberado por unidad, flaggeado
   `<!-- VOICE-RISK: ... -->`; el rubric NO puede fallarlo por sí solo; el Critic lo comenta.
6. **Humanizer conservador**: contrato "conservar, no mejorar". Si una línea no viola
   anti-mediocrity ni style-guide ni voice-profile, SE DEJA. Beats flojos según reader-report
   se flaggean con 2-3 alternativas, no se reescriben unilateralmente. Límite duro: si va a
   tocar >3% de las palabras, para y flaggea al Critic.
7. **Singularity audit** (Continuity Guardian, cada 5 unidades aprobadas): lectura fría sin
   nombres propios — ¿esto lo escribió el personaje/narrador o "un buen escritor genérico del
   registro"? Output: nota advisory con los 2-3 lugares donde la voz es más singular y los
   2-3 donde es más genérica; el humano recalibra voice-profile si quiere.

## 9. Rubric v3 (rubric.md)

- **Nonfiction**: familias v2 (scope, outline, tech_a, tech_b, pedagogy, voice, reader_pov,
  code, consistency, forward_refs) + familia `rhet` (§7) + `profile` (cumplimiento de
  register/citation/closing policy del perfil — 2-3 ítems, significant). `pedagogy-3` se
  REDEFINE: el cierre cumple la closing policy del PERFIL (ya no exige "recap o puente"
  universal). `consistency-1` se REDEFINE: la voz coincide con voice-profile.md (no "con el
  capítulo anterior" — eso premiaba homogeneidad).
- **Literary**: ITEMIZADO por primera vez. Familias: `beats` (outline fidelity),
  `character`, `arc`, `voice` (anti-mediocrity literaria + calibración), `craft` (nuevos:
  craft-1 exposition-as-dialogue significant · craft-2 pause-without-texture significant ·
  craft-3 secondary-without-line minor/significant · craft-4 voice-risk presente
  (observación) · craft-5 escena sin friction inventory significant), `reader_pov`,
  `continuity`, `rhet` (subset: rhet-2, rhet-6 aplican; el resto no).
- Cada ítem: id, name, severity, cómo verificarlo (con comando/conteo cuando sea contable),
  loopback_target. Mismo esquema de scorecard para todos los perfiles.

## 10. Contratos de nombres (para TODO archivo)

- Scorecard: `drafts/unit-NN/scorecard.yaml` (template `templates/scorecard.yaml`).
- `schema_version: "3.0"` en meta.yaml y project-status.yaml. Phase detection: si falta
  meta.yaml → init; si schema ≠ 3.0 → decirle al humano que este proyecto es de una versión
  anterior de la skill y ofrecer recrearlo (NO hay migración automática).
- Modelos: `models: {tiers: {creative: inherit, audit: inherit}, roles: {writer: creative,
  critic: creative, humanizer: <creative en literary, audit en nonfiction>, default: audit}}`.
- Los agentes cargan SIEMPRE, en este orden: (1) su archivo de agente, (2) el perfil,
  (3) meta.yaml, (4) voice-profile.md (agentes de prosa), (5) el resto según su contrato.
- Anti-mediocrity: `anti-mediocrity-nonfiction.md` la leen Writer/Humanizer/Critic/CG-A de
  TODOS los perfiles nonfiction; la literaria, los agentes literarios. Reader-POV y
  Proofreader NO la leen (igual que v2).
- Cost observability: el orquestador (no los agentes) appendea
  `- [unit-NN, writer, creative, 1, 2026-07-03T14:02Z]` a
  `project-status.yaml:runs`. Nada más.

## 11. Estilo de redacción de los archivos

- Imperativo, explicar el POR QUÉ (los archivos v2 lo hacen bien — mantener ese estándar).
- Ejemplos BAD permitidos y bienvenidos; ejemplos GOOD de prosa PROHIBIDOS en references
  (la única excepción: fragmentos de una línea para ilustrar una regla mecánica, ej. "serves
  as → is"). Si necesitás mostrar "cómo sí", describí las propiedades del resultado, no un
  pasaje imitable.
- SKILL.md < 500 líneas. References < 350 líneas c/u; perfiles < 150.
- Nada de changelog dentro de SKILL.md ni de las references.
- Reutilizar lo bueno de v2: cuando el archivo v2 equivalente tiene contenido correcto y
  vigente (ej. grounding pass del writer, axis A/B del reviewer, loopback handoff), adaptarlo,
  no reinventarlo. Corregir las contradicciones detectadas en la auditoría (B1-B8).
