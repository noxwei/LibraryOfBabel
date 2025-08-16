-- =============================================================================
-- 📖 FOUCAULDIAN POWER ANALYSIS & QUEER THEORY ENHANCEMENT
-- =============================================================================
-- Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
-- 
-- CONCEPT: Foucault + queer theory + surveillance + taboo + desire analysis
-- APPROACH: Power relations, surveillance mechanisms, taboo transgressions
-- INNOVATION: Queering traditional academic boundaries through power analysis
-- =============================================================================

-- =============================================================================
-- 🔍 FOUCAULDIAN POWER/SURVEILLANCE ANALYSIS FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION chen_foucauldian_power_analysis(
    p_power_concept TEXT,
    p_surveillance_type TEXT DEFAULT 'panopticon',
    p_resistance_focus TEXT DEFAULT 'biopower',
    p_limit INTEGER DEFAULT 12
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    power_mechanism TEXT,
    surveillance_intensity REAL,
    resistance_potential REAL,
    disciplinary_apparatus TEXT
) AS $$
BEGIN
    -- Foucault principle: Power produces knowledge, knowledge reinforces power
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        b.author,
        LEFT(c.content, 550) as content,
        
        -- Power mechanism: how does power operate here?
        CASE 
            WHEN c.content ~* (p_power_concept || '.*discipline|disciplinary|surveillance|control') THEN 'disciplinary_power'
            WHEN c.content ~* (p_power_concept || '.*knowledge|truth|discourse|expertise') THEN 'power_knowledge'
            WHEN c.content ~* (p_power_concept || '.*body|bodies|embodiment|corporeal') THEN 'biopower'
            WHEN c.content ~* (p_power_concept || '.*govern|government|governmentality|population') THEN 'governmentality'
            WHEN c.content ~* (p_power_concept || '.*subject|subjectification|identity|self') THEN 'subjectification'
            WHEN c.content ~* (p_power_concept || '.*norm|normal|normalization|abnormal') THEN 'normalization'
            ELSE 'sovereign_power'
        END::TEXT as power_mechanism,
        
        -- Surveillance intensity: panopticon effects
        (CASE 
            WHEN c.content ~* 'panopticon|observation|watching|monitor|surveillance|inspect' THEN 1.0
            WHEN c.content ~* 'examination|test|measure|evaluate|assess|judge' THEN 0.9
            WHEN c.content ~* 'record|document|file|archive|register|track' THEN 0.8
            WHEN c.content ~* 'visible|visibility|seen|gaze|look|eye|observ' THEN 0.7
            WHEN c.content ~* 'control|manage|regulate|govern|discipline' THEN 0.6
            ELSE similarity(c.content, 'surveillance apparatus') * 0.5
        END)::REAL as surveillance_intensity,
        
        -- Resistance potential: where power meets resistance
        (CASE 
            WHEN c.content ~* 'resist|resistance|subvert|transgress|counter|oppose' THEN 1.0
            WHEN c.content ~* 'alternative|different|other|else|beyond|outside' THEN 0.9
            WHEN c.content ~* 'question|challenge|critique|doubt|skeptical' THEN 0.8
            WHEN c.content ~* 'freedom|free|liberation|emancipat|autonomy' THEN 0.7
            WHEN c.content ~* 'creative|create|invention|innovation|new' THEN 0.6
            ELSE similarity(c.content, 'lines of flight') * 0.5
        END)::REAL as resistance_potential,
        
        -- Disciplinary apparatus: what institutional forms?
        CASE 
            WHEN c.content ~* 'school|education|pedagogy|student|teacher|learn' THEN 'educational_apparatus'
            WHEN c.content ~* 'hospital|medical|doctor|patient|health|clinic' THEN 'medical_apparatus'
            WHEN c.content ~* 'prison|criminal|law|legal|court|justice|police' THEN 'legal_apparatus'
            WHEN c.content ~* 'factory|work|labor|worker|production|industrial' THEN 'economic_apparatus'
            WHEN c.content ~* 'family|domestic|home|private|personal|intimate' THEN 'familial_apparatus'
            WHEN c.content ~* 'military|war|soldier|defense|security|army' THEN 'military_apparatus'
            WHEN c.content ~* 'church|religious|spiritual|sacred|divine|god' THEN 'religious_apparatus'
            ELSE 'diffuse_apparatus'
        END::TEXT as disciplinary_apparatus
        
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        -- Multiple entry points into power relations
        c.search_vector @@ plainto_tsquery('english', p_power_concept)
        OR c.content % p_power_concept
        OR c.content ~* (p_power_concept || '.*power|control|discipline|surveil')
        OR c.content ~* 'foucault|panopticon|biopower|governmentality|disciplinary'
        OR c.content ~* (p_surveillance_type || '.*' || p_resistance_focus)
        OR c.content ~* 'power.*knowledge|knowledge.*power|discourse.*power'
    )
    AND c.content IS NOT NULL
    AND c.word_count > 100
    ORDER BY surveillance_intensity DESC, resistance_potential DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🏳️‍🌈 QUEER THEORY TABOO & DESIRE ANALYSIS FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION chen_queer_taboo_desire_analysis(
    p_desire_concept TEXT,
    p_taboo_boundary TEXT DEFAULT 'heteronormativity',
    p_queer_strategy TEXT DEFAULT 'subversion',
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    desire_mechanism TEXT,
    taboo_transgression REAL,
    queer_potential REAL,
    normative_disruption TEXT
) AS $$
BEGIN
    -- Queer principle: destabilize normative categories through desire and transgression
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        b.author,
        LEFT(c.content, 500) as content,
        
        -- Desire mechanism: how does desire flow/operate?
        CASE 
            WHEN c.content ~* (p_desire_concept || '.*love|romance|attraction|erotic|sexual') THEN 'erotic_desire'
            WHEN c.content ~* (p_desire_concept || '.*power|control|domination|submission') THEN 'power_desire'
            WHEN c.content ~* (p_desire_concept || '.*knowledge|truth|understanding|discovery') THEN 'epistemic_desire'
            WHEN c.content ~* (p_desire_concept || '.*freedom|liberation|escape|transcendence') THEN 'liberatory_desire'
            WHEN c.content ~* (p_desire_concept || '.*creation|creative|art|beauty|aesthetic') THEN 'creative_desire'
            WHEN c.content ~* (p_desire_concept || '.*connection|intimacy|closeness|touch') THEN 'relational_desire'
            WHEN c.content ~* (p_desire_concept || '.*forbidden|taboo|prohibited|secret') THEN 'transgressive_desire'
            ELSE 'diffuse_desire'
        END::TEXT as desire_mechanism,
        
        -- Taboo transgression: breaking normative boundaries
        (CASE 
            WHEN c.content ~* 'forbidden|taboo|prohibited|censored|banned|illegal' THEN 1.0
            WHEN c.content ~* 'transgress|violate|break|cross|exceed|beyond' THEN 0.9
            WHEN c.content ~* 'subvert|undermine|challenge|disrupt|destabilize' THEN 0.8
            WHEN c.content ~* 'deviant|abnormal|perverse|strange|odd|unusual' THEN 0.7
            WHEN c.content ~* 'secret|hidden|private|concealed|underground' THEN 0.6
            ELSE similarity(c.content, 'normative violation') * 0.5
        END)::REAL as taboo_transgression,
        
        -- Queer potential: capacity for denaturalizing norms
        (CASE 
            WHEN c.content ~* 'queer|lesbian|gay|bisexual|transgender|non.*binary' THEN 1.0
            WHEN c.content ~* 'gender|masculine|feminine|identity|performance|role' THEN 0.9
            WHEN c.content ~* 'heterosexual|homosexual|sexuality|sexual.*identity' THEN 0.8
            WHEN c.content ~* 'binary|categories|classification|normal|natural' THEN 0.7
            WHEN c.content ~* 'performative|performance|repetition|citation|iteration' THEN 0.6
            ELSE similarity(c.content, 'denaturalization') * 0.5
        END)::REAL as queer_potential,
        
        -- Normative disruption: what gets destabilized?
        CASE 
            WHEN c.content ~* 'heteronormativity|heterosexual.*norm|straight.*culture' THEN 'heteronormative_disruption'
            WHEN c.content ~* 'gender.*binary|masculine.*feminine|man.*woman' THEN 'gender_binary_disruption'
            WHEN c.content ~* 'family.*values|traditional.*family|nuclear.*family' THEN 'familial_disruption'
            WHEN c.content ~* 'reproduction|reproductive|procreation|fertility' THEN 'reproductive_disruption'
            WHEN c.content ~* 'public.*private|domestic|sphere|space' THEN 'spatial_disruption'
            WHEN c.content ~* 'identity.*category|fixed.*identity|essential|nature' THEN 'identity_disruption'
            WHEN c.content ~* 'time|temporal|future|past|chronology|linear' THEN 'temporal_disruption'
            ELSE 'diffuse_disruption'
        END::TEXT as normative_disruption
        
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        -- Multiple pathways into queer analysis
        c.search_vector @@ plainto_tsquery('english', p_desire_concept)
        OR c.content % p_desire_concept
        OR c.content ~* (p_desire_concept || '.*desire|love|sexuality|gender|queer')
        OR c.content ~* 'queer|lgbt|gender|sexuality|desire|taboo|transgress'
        OR c.content ~* (p_taboo_boundary || '.*' || p_queer_strategy)
        OR c.content ~* 'heteronormativity|binary|performativity|subversion'
    )
    AND c.content IS NOT NULL
    AND c.word_count > 80
    ORDER BY queer_potential DESC, taboo_transgression DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🌀 RHIZOMATIC DESIRE SURVEILLANCE SYNTHESIS FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION chen_desire_surveillance_synthesis(
    p_synthesis_point TEXT,
    p_power_dimension TEXT DEFAULT 'biopower',
    p_desire_dimension TEXT DEFAULT 'transgressive',
    p_limit INTEGER DEFAULT 8
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    synthesis_pattern TEXT,
    power_desire_intensity REAL,
    surveillance_resistance REAL,
    rhizomatic_flow TEXT
) AS $$
BEGIN
    -- Synthesis principle: power, desire, surveillance in rhizomatic connection
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 450) as content,
        
        -- Synthesis pattern: how do power/desire/surveillance interact?
        CASE 
            WHEN c.content ~* (p_synthesis_point || '.*power.*desire|desire.*power') THEN 'power_desire_circuit'
            WHEN c.content ~* (p_synthesis_point || '.*surveillance.*resist|resist.*surveillance') THEN 'surveillance_resistance_dialectic'
            WHEN c.content ~* (p_synthesis_point || '.*taboo.*surveil|surveil.*taboo') THEN 'taboo_surveillance_nexus'
            WHEN c.content ~* (p_synthesis_point || '.*queer.*power|power.*queer') THEN 'queer_power_assemblage'
            WHEN c.content ~* (p_synthesis_point || '.*desire.*discipline|discipline.*desire') THEN 'desire_discipline_machine'
            WHEN c.content ~* (p_synthesis_point || '.*freedom.*control|control.*freedom') THEN 'freedom_control_paradox'
            ELSE 'emergent_synthesis'
        END::TEXT as synthesis_pattern,
        
        -- Power-desire intensity: mutual reinforcement or tension?
        (similarity(c.content, p_synthesis_point || ' ' || p_power_dimension || ' ' || p_desire_dimension) * 0.5 +
         CASE 
             WHEN c.content ~* 'intensity|intensification|amplify|multiply|reinforce' THEN 0.3
             WHEN c.content ~* 'tension|conflict|contradiction|paradox|ambivalence' THEN 0.2
             ELSE 0
         END)::REAL as power_desire_intensity,
        
        -- Surveillance-resistance ratio
        (CASE 
             WHEN c.content ~* 'surveillance' AND c.content ~* 'resistance' THEN 
                 (length(regexp_replace(c.content, '[^surveillance]', '', 'gi')) + 
                  length(regexp_replace(c.content, '[^resistance]', '', 'gi'))) / 100.0
             WHEN c.content ~* 'surveillance' THEN 0.8
             WHEN c.content ~* 'resistance' THEN 0.6
             ELSE 0.3
         END)::REAL as surveillance_resistance,
        
        -- Rhizomatic flow: direction of connection
        CASE 
            WHEN c.content ~* 'flow|flowing|stream|current|movement|circulation' THEN 'fluid_connection'
            WHEN c.content ~* 'rupture|break|fracture|gap|fissure|crack' THEN 'disruptive_connection'
            WHEN c.content ~* 'multiply|proliferate|spread|expand|grow|ramify' THEN 'proliferative_connection'
            WHEN c.content ~* 'transform|metamorphosis|become|becoming|change' THEN 'transformative_connection'
            WHEN c.content ~* 'underground|hidden|secret|invisible|beneath' THEN 'clandestine_connection'
            ELSE 'emergent_connection'
        END::TEXT as rhizomatic_flow
        
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        -- Synthesis search: connecting across domains
        c.content ~* (p_synthesis_point || '.*' || p_power_dimension || '.*' || p_desire_dimension)
        OR (c.search_vector @@ plainto_tsquery('english', p_synthesis_point) 
            AND (c.content ~* p_power_dimension OR c.content ~* p_desire_dimension))
        OR c.content % (p_synthesis_point || ' ' || p_power_dimension || ' ' || p_desire_dimension)
        OR c.content ~* 'foucault.*queer|queer.*foucault|power.*desire.*surveillance'
        OR c.content ~* 'rhizome.*power|rhizome.*desire|assemblage.*surveillance'
    )
    AND c.content IS NOT NULL
    AND c.word_count > 120
    ORDER BY power_desire_intensity DESC, surveillance_resistance DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 📖 Dr. Sarah Chen PostgreSQL-First Architecture Compliance
-- =============================================================================
COMMENT ON FUNCTION chen_foucauldian_power_analysis(TEXT, TEXT, TEXT, INTEGER) IS 
'Dr. Sarah Chen: Foucauldian power/surveillance analysis with disciplinary apparatus mapping';

COMMENT ON FUNCTION chen_queer_taboo_desire_analysis(TEXT, TEXT, TEXT, INTEGER) IS 
'Dr. Sarah Chen: Queer theory taboo transgression and desire mechanism analysis';

COMMENT ON FUNCTION chen_desire_surveillance_synthesis(TEXT, TEXT, TEXT, INTEGER) IS 
'Dr. Sarah Chen: Rhizomatic synthesis of power, desire, surveillance dynamics';

-- =============================================================================
-- 🏳️‍🌈 FOUCAULDIAN QUEER ENHANCEMENT COMPLETE!
-- =============================================================================
-- 
-- 🎉 CRITICAL THEORY LAYER ACTIVATED!
--
-- New Functions:
-- - chen_foucauldian_power_analysis() - Power/surveillance/disciplinary analysis
-- - chen_queer_taboo_desire_analysis() - Queer theory taboo & desire mapping  
-- - chen_desire_surveillance_synthesis() - Rhizomatic power-desire synthesis
--
-- Usage Examples:
-- SELECT * FROM chen_foucauldian_power_analysis('sexuality', 'panopticon', 'biopower', 8);
-- SELECT * FROM chen_queer_taboo_desire_analysis('love', 'heteronormativity', 'subversion', 6);
-- SELECT * FROM chen_desire_surveillance_synthesis('identity', 'governmentality', 'transgressive', 5);
--
-- 📖 Foucault: Power produces knowledge, surveillance creates subjects!
-- 🏳️‍🌈 Queer: Denaturalize norms, transgress boundaries, multiply desires!
-- 🌀 Synthesis: Rhizomatic flows through power-desire-surveillance assemblages!
-- =============================================================================