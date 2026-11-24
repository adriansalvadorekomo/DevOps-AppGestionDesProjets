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
import tn.esprit.backend.entity.Entreprise;
import tn.esprit.backend.repository.EntrepriseRepository;
import tn.esprit.backend.service.impl.EntrepriseServiceImpl;

@ExtendWith(MockitoExtension.class)
class EntrepriseServiceImplTest {

    @Mock EntrepriseRepository entrepriseRepository;
    @InjectMocks EntrepriseServiceImpl service;

    private final Entreprise entreprise = Entreprise.builder().id(1L).nom("Acme").adresse("Tunis").build();

    @Test
    void addAndUpdateSaveThroughTheRepository() {
        when(entrepriseRepository.save(entreprise)).thenReturn(entreprise);
        assertThat(service.addEntreprise(entreprise)).isSameAs(entreprise);
        assertThat(service.updateEntreprise(entreprise)).isSameAs(entreprise);
    }

    @Test
    void getByIdReturnsTheEntityOrNull() {
        when(entrepriseRepository.findById(1L)).thenReturn(Optional.of(entreprise));
        when(entrepriseRepository.findById(9L)).thenReturn(Optional.empty());
        assertThat(service.getEntrepriseById(1L)).isSameAs(entreprise);
        assertThat(service.getEntrepriseById(9L)).isNull();
    }

    @Test
    void getAllAndDelete() {
        when(entrepriseRepository.findAll()).thenReturn(List.of(entreprise));
        assertThat(service.getAllEntreprises()).containsExactly(entreprise);
        service.deleteEntreprise(1L);
        verify(entrepriseRepository).deleteById(1L);
    }
}
