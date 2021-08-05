from sgtk import Hook

class HieroGetShot(Hook):
   """
   Return a Shotgun Shot dictionary for the given Hiero items
   """

   def execute(self, task, item, data, **kwargs):
       """
       Takes a hiero.core.TrackItem as input and returns a data dictionary for
       the shot to update the cut info for.
       """

       # get the parent entity for the Shot
       parent = self.get_shot_parent(item.parentSequence(), data, item=item)

       # shot parent field
       parent_field = "sg_sequence"

       # grab shot from Shotgun
       sg = self.parent.shotgun
       filter = [
           ["project", "is", self.parent.context.project],
           [parent_field, "is", parent],
           ["code", "is", item.name()],
       ]

       # default the return fields to None to use the python-api default
       fields = kwargs.get("fields", None)
       shots = sg.find("Shot", filter, fields=fields)
       if len(shots) > 1:
           # can not handle multiple shots with the same name
           raise StandardError("Multiple shots named '%s' found", item.name())
       if len(shots) == 0:
           # create shot in shotgun
           shot_data = {
               "code": item.name(),
               parent_field: parent,
               "project": self.parent.context.project,
           }
           shot = sg.create("Shot", shot_data, return_fields=fields)
           self.parent.log_info("Created Shot in Shotgun: %s" % shot_data)
       else:
           shot = shots[0]

       # update the thumbnail for the shot
       upload_thumbnail = kwargs.get("upload_thumbnail", True)
       if upload_thumbnail:
           self.parent.execute_hook(
               "hook_upload_thumbnail",
               entity=shot,
               source=item.source(),
               item=item,
               task=kwargs.get("task")
           )

       return shot

   def get_episode(self, data=None, hiero_sequence=None):
       """
       Return the shotgun episode for the given Nuke Studio items.
       We define this as any tag linked to the sequence that starts
       with 'Ep'.
       """

       # If we had setup Nuke Studio to work in an episode context, then we could
       # grab the episode directly from the current context. However in this example we are not doing this but here
       # would be the code.
       # return self.parent.context.entity

       # stick a lookup cache on the data object.
       if "epi_cache" not in data:
           data["epi_cache"] = {}

       # find episode name from the tags on the sequence
       nuke_studio_episode = None
       for t in hiero_sequence.tags():
           if t.name().startswith('FER_'):
               nuke_studio_episode = t
               break
       if not nuke_studio_episode:
           raise StandardError("No episode has been assigned to the sequence: %s" % hiero_sequence.name())

       # For performance reasons, lets check if we've already added the episode to the cache and reuse it
       # Its not a necessary step, but it speeds things up if we don't have to check shotgun for the episode again
       # this session.
       if nuke_studio_episode.guid() in data["epi_cache"]:
           return data["epi_cache"][nuke_studio_episode.guid()]

       # episode not found in cache, grab it from Shotgun
       sg = self.parent.shotgun
       filters = [
           ["project", "is", self.parent.context.project],
           ["code", "is", nuke_studio_episode.name()],
       ]
       episodes = sg.find("Episode", filters, ["code"])
       if len(episodes) > 1:
           # can not handle multiple episodes with the same name
           raise StandardError("Multiple episodes named '%s' found" % nuke_studio_episode.name())

       if len(episodes) == 0:
           # no episode has previously been created with this name
           # so we must create it in shotgun
           epi_data = {
               "code": nuke_studio_episode.name(),
               "project": self.parent.context.project,
           }
           episode = sg.create("Episode", epi_data)
           self.parent.log_info("Created Episode in Shotgun: %s" % epi_data)
       else:
           # we found one episode matching this name in shotgun, so we will resuse it, instead of creating a new one
           episode = episodes[0]

       # update the cache with the results
       data["epi_cache"][nuke_studio_episode.guid()] = episode

       return episode

   def get_shot_parent(self, hiero_sequence, data, **kwargs):
       """
       Given a Hiero sequence and data cache, return the corresponding entity
       in Shotgun to serve as the parent for contained Shots.

       :param hiero_sequence: A Hiero sequence object
       :param data: A dictionary with cached parent data.

       The data dict is typically the app's preprocess_data which maintains        the cache across invocations of this hook.        """
       # stick a lookup cache on the data object.
       #
       if "parent_cache" not in data:
           data["parent_cache"] = {}
       if hiero_sequence.guid() in data["parent_cache"]:
           return data["parent_cache"][hiero_sequence.guid()]


       episode = self.get_episode(data, hiero_sequence)

       # parent not found in cache, grab it from Shotgun
       sg = self.parent.shotgun

       filter = [
           ["project", "is", self.parent.context.project],
           ["code", "is", hiero_sequence.name()],
           ["episode", "is", episode],
       ]





       # the entity type of the parent




       par_entity_type = "Sequence"
       parents = sg.find(par_entity_type, filter)

       if len(parents) > 1:
       # can not handle multiple parents with the same name raise
            StandardError( "Multiple %s entities named '%s' found" % (par_entity_type, hiero_sequence.name()) )
       if len(parents) == 0: #
           #create the parent in shotgun
           par_data = {
               "code": hiero_sequence.name(),
               "project": self.parent.context.project,
               "episode": episode,
           }
           parent = sg.create(par_entity_type, par_data)
           self.parent.log_info( "Created %s in Shotgun: %s" % (par_entity_type, par_data))
       else:
           parent = parents[0]
       # update the thumbnail for the parent
       upload_thumbnail = kwargs.get("upload_thumbnail", True)
       if upload_thumbnail:
           self.parent.execute_hook(
               "hook_upload_thumbnail",
               entity=parent,
               source=hiero_sequence,
               item=None )
       # cache the results
       data["parent_cache"][hiero_sequence.guid()] = parent

       return parent