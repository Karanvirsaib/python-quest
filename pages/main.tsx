import React from 'react';
import {createRoot} from 'react-dom/client';
import Quest from '../app/quest';
import '../app/globals.css';
const base = (import.meta as ImportMeta & {env:{BASE_URL:string}}).env.BASE_URL;
createRoot(document.getElementById('root')!).render(<Quest user={{name:'Explorer',email:'Browser profile · saved on this device'}} storageMode="browser" assetBase={base}/>);
