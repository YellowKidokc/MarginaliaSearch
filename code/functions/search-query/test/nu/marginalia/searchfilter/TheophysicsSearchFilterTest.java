package nu.marginalia.searchfilter;

import nu.marginalia.functions.searchquery.searchfilter.SearchFilterParser;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class TheophysicsSearchFilterTest {
    @Test void transparentProfileParsesWithoutWorldviewAgreementRule() throws Exception {
        var stream = getClass().getResourceAsStream("/filters/theophysics.xml");
        assertNotNull(stream);
        var xml = new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        var spec = new SearchFilterParser().parse("SYSTEM", "THEOPHYSICS", xml);
        assertEquals(3, spec.termsPromote().size());
        assertTrue(spec.termsRequire().isEmpty());
        assertTrue(spec.termsExclude().isEmpty());
        assertFalse(xml.toLowerCase().contains("christian"));
    }
}
