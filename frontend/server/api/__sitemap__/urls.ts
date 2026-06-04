import { queryCollection } from '@nuxt/content/server'
import { defineSitemapEventHandler } from '#imports'

export default defineSitemapEventHandler(async (event) => {
  const posts = await queryCollection(event, 'blog')
    .select('path', 'date')
    .order('date', 'DESC')
    .all()

  return posts.map((post) => ({
    loc: post.path,
    lastmod: post.date,
  }))
})
