package tn.esprit.backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import tn.esprit.backend.entity.Projet;
import tn.esprit.backend.entity.ProjetDetaille;
import tn.esprit.backend.repository.ProjetDetailleRepository;
import tn.esprit.backend.repository.ProjetRepository;
import tn.esprit.backend.service.impl.ProjetDetailleServiceImpl;

@ExtendWith(MockitoExtension.class)
class ProjetDetailleServiceImplTest {

    @Mock ProjetDetailleRepository projetDetailleRepository;
    @Mock ProjetRepository projetRepository;
    @InjectMocks ProjetDetailleServiceImpl service;

    private final ProjetDetaille detail = ProjetDetaille.builder()
            .id(1L).description("API layer").technologie("Spring Boot")
            .coutProvisoire(12000.0).dateDebut(LocalDate.of(2026, 9, 1)).build();

    @Test
    void crudGoesThroughTheRepository() {
        when(projetDetailleRepository.save(detail)).thenReturn(detail);
        when(projetDetailleRepository.findById(1L)).thenReturn(Optional.of(detail));
        when(projetDetailleRepository.findAll()).thenReturn(List.of(detail));
        assertThat(service.addProjetDetaille(detail)).isSameAs(detail);
        assertThat(service.updateProjetDetaille(detail)).isSameAs(detail);
        assertThat(service.getProjetDetailleById(1L)).isSameAs(detail);
        assertThat(service.getAllProjetsDetailles()).containsExactly(detail);
        service.deleteProjetDetaille(1L);
        verify(projetDetailleRepository).deleteById(1L);
    }

    @Test
    void listsTheDetailsOfAProject() {
        when(projetDetailleRepository.findByProjetId(3L)).thenReturn(List.of(detail));
        assertThat(service.getProjetDetaillesByProjet(3L)).containsExactly(detail);
    }

    @Test
    void assignsADetailToAProject() {
        Projet erp = Projet.builder().id(3L).sujet("ERP").build();
        when(projetDetailleRepository.findById(1L)).thenReturn(Optional.of(detail));
        when(projetRepository.findById(3L)).thenReturn(Optional.of(erp));
        when(projetDetailleRepository.save(any(ProjetDetaille.class))).thenAnswer(inv -> inv.getArgument(0));
        assertThat(service.assignProjetDetailleToProjet(1L, 3L).getProjet()).isSameAs(erp);
    }
}
