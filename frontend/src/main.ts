import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { appConfig } from './app/app.config';
import { FaIconLibrary } from '@fortawesome/angular-fontawesome';
import { fas } from '@fortawesome/free-solid-svg-icons';

bootstrapApplication(AppComponent, appConfig)
  .then(appRef => {
    const library = appRef.injector.get(FaIconLibrary);
    library.addIconPacks(fas); // Font Awesome Icons hinzufügen
  })
  .catch(err => console.error(err));
