<template>
    <div class="translate_wrapper">
        <div class="translate_wrapper " :class="{ 'active': isActive }">
            <div class="current_lang">
                <div class="lang"><i class="flag-icon" :class="this.langIcon" @click="display()"></i><span
                        class="lang-txt">{{ langLangauge }}</span></div>
            </div>

            <div class="more_lang" :class="{ 'active': isActive }">
                <div class="lang" v-for="(lang, index) in localOptions" :key="index"><i class="flag-icon "
                        :class="lang.icon"></i><span class="lang-txt" @click.prevent="changeLocale(lang, lang.name)">{{
                            lang.name
                        }}<span>
                            {{ lang.short }}</span></span></div>
            </div>

        </div>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { localeOptions } from '../../constants/config';

export default {
    name: 'languagePage',
    data() {
        return {
            isActive: false,
            localOptions: localeOptions,
        };
    },
    methods: {
        display() {
            this.isActive = !this.isActive
        },
        changeLocale(value, language) {
            this.$i18n.locale = language
            this.$store.dispatch('setLang', value);

        },
    },
    computed: {
        ...mapGetters({
            langIcon: 'langIcon',
            langLangauge: 'langLangauge'
        })
    },
    mounted() {
        this.$store.dispatch('setLang', { name: localStorage.getItem('currentLanguage') || 'EN', icon: localStorage.getItem('currentLanguageIcon') || 'flag-icon-us' })
    }
}
</script>

