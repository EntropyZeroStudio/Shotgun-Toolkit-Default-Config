from sgtk import Hook


class HieroResolveCustomStrings(Hook):
    """Translates a keyword string into its resolved value for a given task."""
    # cache of shots that have already been pulled from shotgun
    _sg_lookup_cache = {}

    def execute(self, task, keyword, **kwargs):
        """
        The default implementation of the custom resolver simply looks up
        the keyword from the shotgun shot dictionary.

        For example, to pull the shot code, you would simply specify 'code'.
        To pull the sequence code you would use 'sg_sequence.Sequence.code'.
        """

        if keyword == "{Episode}":
            episode_entity = self.parent.execute_hook_method(
                "hook_get_shot",
                "get_episode",
                data=self.parent.preprocess_data,
                hiero_sequence=task._item.parentSequence(),
            )
            # hard coded to return the name of the episode
            # if however your folder for the episode in the schema, is not just made up from the code field
            # you need to get it to return what ever string value the folder would normally be created with.
            return episode_entity['code']

        shot_code = task._item.name()

        # grab the shot from the cache, or the get_shot hook if not cached
        sg_shot = self._sg_lookup_cache.get(shot_code)
        if sg_shot is None:
            fields = [ctf['keyword'] for ctf in self.parent.get_setting('custom_template_fields')]
            sg_shot = self.parent.execute_hook(
                "hook_get_shot",
                task=task,
                item=task._item,
                data=self.parent.preprocess_data,
                fields=fields,
                upload_thumbnail=False,
            )

            self._sg_lookup_cache[shot_code] = sg_shot

        self.parent.log_info("_sg_lookup_cache: %s" % (self._sg_lookup_cache))

        if sg_shot is None:
            raise RuntimeError("Could not find shot for custom resolver: %s" % keyword)

        # strip off the leading and trailing curly brackets
        keyword = keyword[1:-1]
        result = sg_shot.get(keyword, "")

        self.parent.log_debug("Custom resolver: %s[%s] -> %s" % (shot_code, keyword, result))

        return result