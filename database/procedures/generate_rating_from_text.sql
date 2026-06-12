-- Keyword Sentiment Function

CREATE OR REPLACE FUNCTION niche_data.generate_rating_from_text(p_text TEXT)
RETURNS INT AS $$
DECLARE
    v_rating INT := 3; -- neutral baseline
BEGIN
    IF p_text ~* '(amazing|excellent|perfect|love|great|awesome)' THEN
        v_rating := 5;
    ELSIF p_text ~* '(good|nice|satisfied|fine|ok)' THEN
        v_rating := 4;
    ELSIF p_text ~* '(bad|poor|disappointed|not good|cheap)' THEN
        v_rating := 2;
    ELSIF p_text ~* '(terrible|awful|worst|hate|broken)' THEN
        v_rating := 1;
    END IF;

    RETURN v_rating;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
