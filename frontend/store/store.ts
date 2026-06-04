import { reactive } from 'vue';

// Define an interface to describe the shape of the store object
interface StoreState {
    darkMode: boolean;
}

export const store = reactive<StoreState>({
    darkMode: false
});
