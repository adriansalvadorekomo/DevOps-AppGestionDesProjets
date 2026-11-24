package tn.esprit.backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import tn.esprit.backend.entity.Entreprise;
import tn.esprit.backend.entity.Equipe;
import tn.esprit.backend.entity.Projet;
import tn.esprit.backend.repository.EntrepriseRepository;
import tn.esprit.backend.repository.EquipeRepository;
import tn.esprit.backend.repository.ProjetRepository;
import tn.esprit.backend.service.impl.EquipeServiceImpl;

@ExtendWith(MockitoExtension.class)
class EquipeServiceImplTest {

    @Mock EquipeRepository equipeRepository;
    @Mock EntrepriseRepository entrepriseRepository;
    @Mock ProjetRepository projetRepository;
    @InjectMocks EquipeServiceImpl service;

    private Equipe equipe() {
        return Equipe.builder().id(1L).nom("Data").specialite("ETL").projets(new ArrayList<>()).build();
    }

    @Test
    void crudGoesThroughTheRepository() {
        Equipe e = equipe();
        when(equipeRepository.save(e)).thenReturn(e);
        when(equipeRepository.findById(1L)).thenReturn(Optional.of(e));
        when(equipeRepository.findAll()).thenReturn(List.of(e));
        assertThat(service.addEquipe(e)).isSameAs(e);
        assertThat(service.updateEquipe(e)).isSameAs(e);
        assertThat(service.getEquipeById(1L)).isSameAs(e);
        assertThat(service.getAllEquipes()).containsExactly(e);
        service.deleteEquipe(1L);
        verify(equipeRepository).deleteById(1L);
    }

    @Test
    void listsTheTeamsOfACompany() {
        Equipe e = equipe();
        when(equipeRepository.findByEntrepriseId(7L)).thenReturn(List.of(e));
        assertThat(service.getEquipesByEntreprise(7L)).containsExactly(e);
    }

    @Test
    void assignsATeamToACompany() {
        Equipe e = equipe();
        Entreprise acme = Entreprise.builder().id(7L).nom("Acme").build();
        when(equipeRepository.findById(1L)).thenReturn(Optional.of(e));
        when(entrepriseRepository.findById(7L)).thenReturn(Optional.of(acme));
        when(equipeRepository.save(any(Equipe.class))).thenAnswer(inv -> inv.getArgument(0));
        assertThat(service.assignEquipeToEntreprise(1L, 7L).getEntreprise()).isSameAs(acme);
    }

    @Test
    void assignsATeamToAProject() {
        Equipe e = equipe();
        Projet erp = Projet.builder().id(3L).sujet("ERP").build();
        when(equipeRepository.findById(1L)).thenReturn(Optional.of(e));
        when(projetRepository.findById(3L)).thenReturn(Optional.of(erp));
        when(equipeRepository.save(any(Equipe.class))).thenAnswer(inv -> inv.getArgument(0));
        assertThat(service.assignEquipeToProjet(1L, 3L).getProjets()).containsExactly(erp);
    }
}
