package tn.esprit.backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import tn.esprit.backend.entity.Projet;
import tn.esprit.backend.repository.ProjetRepository;
import tn.esprit.backend.service.impl.ProjetServiceImpl;

@ExtendWith(MockitoExtension.class)
class ProjetServiceImplTest {

    @Mock ProjetRepository projetRepository;
    @InjectMocks ProjetServiceImpl service;

    private final Projet projet = Projet.builder().id(1L).sujet("ERP migration").build();

    @Test
    void addAndUpdateSaveThroughTheRepository() {
        when(projetRepository.save(projet)).thenReturn(projet);
        assertThat(service.addProjet(projet)).isSameAs(projet);
        assertThat(service.updateProjet(projet)).isSameAs(projet);
    }

    @Test
    void getByIdReturnsTheEntityOrNull() {
        when(projetRepository.findById(1L)).thenReturn(Optional.of(projet));
        when(projetRepository.findById(2L)).thenReturn(Optional.empty());
        assertThat(service.getProjetById(1L)).isSameAs(projet);
        assertThat(service.getProjetById(2L)).isNull();
    }

    @Test
    void getAllAndDelete() {
        when(projetRepository.findAll()).thenReturn(List.of(projet));
        assertThat(service.getAllProjets()).containsExactly(projet);
        service.deleteProjet(1L);
        verify(projetRepository).deleteById(1L);
    }
}
