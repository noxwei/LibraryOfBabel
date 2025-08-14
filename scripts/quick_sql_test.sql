-- Quick test of all 10 Dr. Chen functions
-- Each query limited to 1 result with simple terms

\echo '🧠 DR. CHEN FUNCTION TESTING'
\echo '============================'

\echo '1. Rhizomatic exploration...'
SELECT COUNT(*) as rhizomatic_count FROM chen_rhizomatic_exploration('love', 'any', 1, 1);

\echo '2. Sci-fi bridges...'
SELECT COUNT(*) as scifi_count FROM chen_scifi_speculative_bridges('robot', 'future', 1);

\echo '3. Fantasy resonance...'
SELECT COUNT(*) as fantasy_count FROM chen_fantasy_mythic_resonance('hero', 'quest', 1);

\echo '4. Genre transcendence...'
SELECT COUNT(*) as genre_count FROM chen_genre_transcendence('magic', 1);

\echo '5. Foucauldian power...'
SELECT COUNT(*) as power_count FROM chen_foucauldian_power_analysis('power', 'control', 'resist', 1);

\echo '6. Queer desire...'
SELECT COUNT(*) as queer_count FROM chen_queer_taboo_desire_analysis('desire', 'norm', 'queer', 1);

\echo '7. Desire synthesis...'
SELECT COUNT(*) as synthesis_count FROM chen_desire_surveillance_synthesis('identity', 'power', 'desire', 1);

\echo '8. Analogical search...'
SELECT COUNT(*) as analogical_count FROM chen_analogical_search('decision', 'philosophy', 'tech', 1);

\echo '9. Conceptual bridges...'
SELECT COUNT(*) as bridges_count FROM chen_find_conceptual_bridges('math', 'art', 1);

\echo '10. Analogical patterns...'
SELECT COUNT(*) as patterns_count FROM chen_analogical_patterns('network', 'biology', 1);

\echo 'Testing complete!'