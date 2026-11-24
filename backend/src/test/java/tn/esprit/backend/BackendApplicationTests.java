package tn.esprit.backend;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import tn.esprit.backend.controller.EquipeController;
import tn.esprit.backend.service.IEquipeService;

@SpringBootTest
class BackendApplicationTests {

    @Autowired EquipeController equipeController;
    @Autowired IEquipeService equipeService;

    @Test
    void contextLoadsAndWiresTheWebLayerToTheServices() {
        assertThat(equipeController).isNotNull();
        assertThat(equipeService).isNotNull();
    }
}
